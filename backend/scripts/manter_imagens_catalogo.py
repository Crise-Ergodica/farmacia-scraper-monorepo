"""Bounded image recovery and URL monitoring; safe to schedule repeatedly."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.catalogo import CatalogoBase
from app.models.oferta_farmacia import OfertaFarmacia
from app.services.imagens import (
    register_image_candidate,
    validate_image_association,
    verify_image_url,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("preco_bao.image_maintenance")


@dataclass(frozen=True)
class ImageCandidate:
    url: str
    pharmacy: str
    sku: str | None
    ean: str | None
    product_url: str
    catalog_id: int


@dataclass(frozen=True)
class CatalogSnapshot:
    id: int
    url: str
    ean: str | None
    source: str | None
    sku: str | None
    match: str | None
    failures: int
    alternatives: tuple[ImageCandidate, ...]


class HostPacer:
    def __init__(self, minimum_interval: float) -> None:
        self.minimum_interval = minimum_interval
        self._next: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, host: str) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next.get(host, now) - now)
            if delay:
                await asyncio.sleep(delay)
            self._next[host] = time.monotonic() + self.minimum_interval


def load_snapshots(
    *, limit: int, recheck_hours: int, pending_only: bool
) -> list[CatalogSnapshot]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=recheck_hours)
    with SessionLocal() as db:
        statement = (
            select(CatalogoBase)
            .options(
                selectinload(CatalogoBase.ofertas).selectinload(OfertaFarmacia.farmacia)
            )
            .order_by(CatalogoBase.id)
        )
        if pending_only:
            statement = statement.where(CatalogoBase.imagem_url.is_(None))
        else:
            statement = statement.where(
                CatalogoBase.imagem_url.is_not(None),
                or_(
                    CatalogoBase.imagem_ultima_verificacao_em.is_(None),
                    CatalogoBase.imagem_ultima_verificacao_em <= cutoff,
                ),
            ).order_by(
                CatalogoBase.imagem_ultima_verificacao_em.asc().nulls_first(),
                CatalogoBase.id,
            )
        products = db.execute(statement.limit(limit)).scalars().all()
        snapshots: list[CatalogSnapshot] = []
        for product in products:
            candidates: list[ImageCandidate] = []
            for offer in product.ofertas:
                pharmacy = offer.farmacia.nome_fantasia if offer.farmacia else ""
                if not offer.imagem_url or not pharmacy or not offer.url_origem:
                    continue
                valid, match, _ = validate_image_association(
                    image_url=offer.imagem_url,
                    pharmacy_name=pharmacy,
                    sku=offer.sku_interno,
                    ean=product.codigo_barras,
                    product_url=offer.url_origem,
                    identity_confirmed=True,
                )
                if valid:
                    candidates.append(
                        ImageCandidate(
                            offer.imagem_url,
                            pharmacy,
                            offer.sku_interno,
                            product.codigo_barras,
                            offer.url_origem,
                            product.id,
                        )
                    )
            snapshots.append(
                CatalogSnapshot(
                    product.id,
                    product.imagem_url or "",
                    product.codigo_barras,
                    product.imagem_fonte,
                    product.imagem_sku_origem,
                    product.imagem_match,
                    product.imagem_falhas_consecutivas or 0,
                    tuple(candidates),
                )
            )
        return snapshots


async def verify_bounded(url: str, *, semaphore: asyncio.Semaphore, pacer: HostPacer):
    from urllib.parse import urlsplit

    async with semaphore:
        await pacer.wait((urlsplit(url).hostname or "").lower())
        return await verify_image_url(url, timeout_seconds=8)


def should_try_alternative(
    *, status_code: int | None, consecutive_failures: int, failure_threshold: int
) -> bool:
    """Switch only for definitive 403/404 or a repeated failure threshold."""
    return status_code in {403, 404} or consecutive_failures + 1 >= failure_threshold


async def check_images(args: argparse.Namespace) -> int:
    if os.getenv("IMAGE_MONITOR_ENABLED", "true").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        logger.info("IMAGE_MONITOR_ENABLED=false; nenhuma URL foi consultada.")
        return 0

    snapshots = load_snapshots(
        limit=args.limit, recheck_hours=args.recheck_hours, pending_only=False
    )
    if not snapshots:
        logger.info("Nenhuma referência venceu a janela de revalidação.")
        return 0
    semaphore = asyncio.Semaphore(args.concurrency)
    pacer = HostPacer(args.host_interval)

    async def process(snapshot: CatalogSnapshot) -> dict:
        current = await verify_bounded(snapshot.url, semaphore=semaphore, pacer=pacer)
        if not current.ok and current.status_code is None:
            await asyncio.sleep(1)
            current = await verify_bounded(
                snapshot.url, semaphore=semaphore, pacer=pacer
            )
        replacement: ImageCandidate | None = None
        replacement_check = None
        if not current.ok and should_try_alternative(
            status_code=current.status_code,
            consecutive_failures=snapshot.failures,
            failure_threshold=args.failure_threshold,
        ):
            for candidate in snapshot.alternatives:
                if candidate.url == snapshot.url:
                    continue
                result = await verify_bounded(
                    candidate.url, semaphore=semaphore, pacer=pacer
                )
                if result.ok:
                    replacement, replacement_check = candidate, result
                    break
        return {
            "snapshot": snapshot,
            "check": current,
            "replacement": replacement,
            "replacement_check": replacement_check,
        }

    outcomes = await asyncio.gather(*(process(snapshot) for snapshot in snapshots))
    now = datetime.now(UTC)
    checked_ok = 0
    replaced = 0
    failures = 0
    with SessionLocal() as db:
        for outcome in outcomes:
            snapshot: CatalogSnapshot = outcome["snapshot"]
            product = db.get(CatalogoBase, snapshot.id)
            if product is None or product.imagem_url != snapshot.url:
                logger.warning(
                    "Imagem mudou durante a verificação; ignorando catálogo %s",
                    snapshot.id,
                )
                continue
            current = outcome["check"]
            candidate: ImageCandidate | None = outcome["replacement"]
            if current.ok:
                product.imagem_verificada_em = now
                product.imagem_ultima_verificacao_em = now
                product.imagem_status = "verificada"
                product.imagem_falhas_consecutivas = 0
                product.imagem_ultima_falha = None
                checked_ok += 1
                continue
            if candidate is not None:
                product.imagem_url = candidate.url
                product.imagem_fonte = outcome["replacement_check"].source
                product.imagem_sku_origem = candidate.sku
                product.imagem_ean = candidate.ean
                valid, match, _ = validate_image_association(
                    image_url=candidate.url,
                    pharmacy_name=candidate.pharmacy,
                    sku=candidate.sku,
                    ean=candidate.ean,
                    product_url=candidate.product_url,
                    identity_confirmed=True,
                )
                if not valid:
                    continue
                product.imagem_match = match
                product.imagem_status = "verificada"
                product.imagem_verificada_em = now
                product.imagem_ultima_verificacao_em = now
                product.imagem_atualizada_em = now
                product.imagem_falhas_consecutivas = 0
                product.imagem_ultima_falha = None
                product.imagem_motivo_rejeicao = None
                replaced += 1
                continue
            product.imagem_ultima_verificacao_em = now
            product.imagem_falhas_consecutivas = snapshot.failures + 1
            product.imagem_ultima_falha = (
                current.reason or "Falha temporária sem detalhe HTTP."
            )
            if product.imagem_falhas_consecutivas >= args.failure_threshold:
                product.imagem_status = "indisponivel"
            failures += 1
        db.commit()

    logger.info(
        "Verificação: lote=%s válidas=%s substituídas=%s falhas=%s",
        len(outcomes),
        checked_ok,
        replaced,
        failures,
    )
    return 0


async def recover_pending(args: argparse.Namespace) -> int:
    if os.getenv("IMAGE_RECOVERY_ENABLED", "true").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        logger.info(
            "IMAGE_RECOVERY_ENABLED=false; nenhum item pendente foi consultado."
        )
        return 0
    snapshots = load_snapshots(limit=args.limit, recheck_hours=24, pending_only=True)
    semaphore = asyncio.Semaphore(args.concurrency)
    pacer = HostPacer(args.host_interval)

    async def find_candidate(snapshot: CatalogSnapshot):
        for candidate in snapshot.alternatives:
            result = await verify_bounded(
                candidate.url, semaphore=semaphore, pacer=pacer
            )
            if result.ok:
                return candidate, result
        return None

    results = await asyncio.gather(*(find_candidate(item) for item in snapshots))
    attached = 0
    with SessionLocal() as db:
        for snapshot, result in zip(snapshots, results, strict=True):
            if result is None:
                continue
            candidate, check = result
            product = db.get(CatalogoBase, snapshot.id)
            if product is None or product.imagem_url:
                continue
            accepted = register_image_candidate(
                product,
                image_url=candidate.url,
                pharmacy_name=candidate.pharmacy,
                sku=candidate.sku,
                ean=candidate.ean,
                product_url=candidate.product_url,
                identity_confirmed=True,
            )
            if accepted:
                product.imagem_status = "verificada"
                product.imagem_verificada_em = datetime.now(UTC)
                product.imagem_ultima_verificacao_em = datetime.now(UTC)
                product.imagem_falhas_consecutivas = 0
                product.imagem_ultima_falha = None
                attached += 1
        db.commit()
    logger.info(
        "Pendências: consultadas=%s referências_recuperadas=%s",
        len(snapshots),
        attached,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check", help="Verificar e recuperar URLs já persistidas"
    )
    check.add_argument(
        "--limit", type=int, default=int(os.getenv("IMAGE_MONITOR_BATCH_SIZE", "100"))
    )
    check.add_argument(
        "--recheck-hours",
        type=int,
        default=int(os.getenv("IMAGE_MONITOR_RECHECK_HOURS", "24")),
    )
    check.add_argument("--failure-threshold", type=int, default=3)
    check.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("IMAGE_MONITOR_CONCURRENCY", "4")),
    )
    check.add_argument(
        "--host-interval",
        type=float,
        default=float(os.getenv("IMAGE_MONITOR_HOST_INTERVAL", "0.5")),
    )
    pending = commands.add_parser(
        "recover-pending", help="Tentar imagens de ofertas em produtos sem referência"
    )
    pending.add_argument(
        "--limit", type=int, default=int(os.getenv("IMAGE_RECOVERY_BATCH_SIZE", "100"))
    )
    pending.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("IMAGE_MONITOR_CONCURRENCY", "4")),
    )
    pending.add_argument(
        "--host-interval",
        type=float,
        default=float(os.getenv("IMAGE_MONITOR_HOST_INTERVAL", "0.5")),
    )
    args = parser.parse_args()
    parser.exit(
        2,
        "Este comando foi desativado: as imagens agora usam o registro externo "
        "backend/data/image_references/references.json e n??o devem ser gravadas "
        "no PostgreSQL.\n",
    )
    if args.limit < 1 or args.concurrency < 1 or args.host_interval < 0:
        parser.error(
            "limit/concurrency precisam ser positivos; intervalo deve ser >= 0"
        )
    return asyncio.run(
        check_images(args) if args.command == "check" else recover_pending(args)
    )


if __name__ == "__main__":
    raise SystemExit(main())
