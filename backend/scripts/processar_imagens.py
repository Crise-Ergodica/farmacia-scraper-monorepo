"""Resumable catalog image audit using exact pharmacy SKU/EAN identity."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import CatalogoBase, Farmacia, OfertaFarmacia
from app.services.imagens import (
    image_rejection_reason,
    select_vtex_item_image,
    validate_image_association,
    verify_image_url,
)

API_URL = "https://www.farmaciaindiana.com.br/api/catalog_system/pub/products/search/medicamentos"
SKU_API_URL = (
    "https://www.farmaciaindiana.com.br/api/catalog_system/pub/products/search"
)
STATE_PATH = Path(__file__).resolve().parents[1] / ".image_audit_state.json"
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "image-audit.json"


def save_state(state: dict) -> None:
    temporary_path = STATE_PATH.with_name(f".image_audit_state.{os.getpid()}.tmp")
    temporary_path.write_text(json.dumps(state), encoding="utf-8")
    temporary_path.replace(STATE_PATH)


def normalized(value: str) -> str:
    decomposed = (
        unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode().lower()
    )
    return re.sub(r"[^a-z0-9]+", " ", decomposed).strip()


async def discover_indiana(state: dict) -> dict[str, list[dict]]:
    by_ean: dict[str, list[dict]] = state.setdefault("indiana_by_ean", {})
    by_name: dict[str, list[dict]] = state.setdefault("indiana_by_name", {})
    if state.get("indiana_complete"):
        return by_ean

    offset = int(state.get("indiana_offset", 0))
    async with httpx.AsyncClient(timeout=25, follow_redirects=False) as client:
        while True:
            end = offset + 49
            response = await client.get(API_URL, params={"_from": offset, "_to": end})
            response.raise_for_status()
            products = response.json()
            if not products:
                state["indiana_complete"] = True
                break
            for product in products:
                name = str(product.get("productName") or "")
                for item in product.get("items") or []:
                    ean = str(item.get("ean") or "").strip()
                    item_id = str(item.get("itemId") or "").strip()
                    record = {
                        "item": item,
                        "name": name,
                        "sku": item_id,
                        "link": product.get("link"),
                    }
                    if ean:
                        by_ean.setdefault(ean, []).append(record)
                    by_name.setdefault(normalized(name), []).append(record)
            offset += 50
            state["indiana_offset"] = offset
            save_state(state)
            await asyncio.sleep(1.0)
    return by_ean


async def lookup_indiana_sku(sku: str, state: dict) -> dict | None:
    cache: dict[str, dict | None] = state.setdefault("indiana_by_sku", {})
    if sku in cache:
        return cache[sku]
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            response = await client.get(
                SKU_API_URL,
                params={"fq": f"skuId:{sku}"},
            )
            response.raise_for_status()
            products = response.json()
        exact = next(
            (
                {
                    "item": item,
                    "name": product.get("productName"),
                    "sku": sku,
                    "link": product.get("link"),
                }
                for product in products
                for item in product.get("items") or []
                if str(item.get("itemId") or "") == sku
            ),
            None,
        )
        cache[sku] = exact
        await asyncio.sleep(0.25)
        return exact
    except (httpx.HTTPError, ValueError) as exc:
        state.setdefault("indiana_sku_errors", {})[sku] = type(exc).__name__
        return None


async def main(
    limit: int | None = None,
    no_discovery: bool = False,
    recheck_verified: bool = False,
    retry_discovery: bool = False,
) -> None:
    try:
        state = (
            json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if STATE_PATH.exists()
            else {}
        )
    except (json.JSONDecodeError, OSError):
        state = {}
    if retry_discovery:
        state.pop("discovery_error", None)
        state.pop("discovery_http_status", None)
        save_state(state)
    db = SessionLocal()
    if "baseline" not in state:
        total = db.query(CatalogoBase).count()
        with_offer_image = (
            db.query(func.count(func.distinct(OfertaFarmacia.catalogo_id)))
            .filter(OfertaFarmacia.imagem_url.is_not(None))
            .scalar()
            or 0
        )
        state["baseline"] = {
            "catalog_total": total,
            "catalog_items_with_offer_image": with_offer_image,
            "catalog_items_without_offer_image": total - with_offer_image,
            "verified_catalog_images": db.query(CatalogoBase)
            .filter(CatalogoBase.imagem_status == "verificada")
            .count(),
        }
        save_state(state)
    db.close()

    if (
        not no_discovery
        and not state.get("indiana_complete")
        and not state.get("discovery_error")
    ):
        try:
            await discover_indiana(state)
        except Exception as exc:
            state["discovery_error"] = type(exc).__name__
            state["discovery_http_status"] = getattr(
                getattr(exc, "response", None), "status_code", None
            )
            state["discovery_complete"] = False
            save_state(state)
            print(
                f"Indiana public search stopped ({type(exc).__name__}); "
                "auditing local offers and collected pages.",
                flush=True,
            )

    processed: set[str] = (
        set() if recheck_verified else set(state.get("processed_ids", []))
    )
    rejected: dict[str, str] = state.get("rejected", {})
    recovered: dict[str, dict] = state.get("recovered", {})
    query = select(CatalogoBase).order_by(CatalogoBase.id)
    if limit:
        query = query.limit(limit)
    db = SessionLocal()
    try:
        medicines = db.execute(query).scalars().all()
        offers = db.execute(
            select(OfertaFarmacia, Farmacia.nome_fantasia).join(
                Farmacia, Farmacia.id == OfertaFarmacia.farmacia_id
            )
        ).all()
        offers_by_catalog: dict[int, list[tuple[OfertaFarmacia, str | None]]] = {}
        for offer, pharmacy_name in offers:
            offers_by_catalog.setdefault(offer.catalogo_id, []).append(
                (offer, pharmacy_name)
            )

        targets = []
        for medicine in medicines:
            key = str(medicine.id)
            if key in processed or (
                medicine.imagem_status == "verificada" and not recheck_verified
            ):
                continue
            candidates = []
            indiana_skus = set()
            if medicine.imagem_url:
                candidates.append(
                    (
                        medicine.imagem_url,
                        medicine.imagem_fonte,
                        medicine.imagem_sku_origem,
                        medicine.imagem_ean,
                        medicine.imagem_match or "sku",
                    )
                )
            for offer, pharmacy_name in offers_by_catalog.get(medicine.id, []):
                if (offer.sku_interno or "").startswith("IND"):
                    indiana_skus.add(offer.sku_interno[3:])
                if not offer.imagem_url:
                    continue
                valid, match, reason = validate_image_association(
                    image_url=offer.imagem_url,
                    pharmacy_name=pharmacy_name or "",
                    sku=offer.sku_interno,
                    ean=medicine.codigo_barras,
                    product_url=offer.url_origem,
                )
                if valid:
                    candidates.append(
                        (
                            offer.imagem_url,
                            pharmacy_name,
                            offer.sku_interno,
                            medicine.codigo_barras,
                            match or "sku",
                        )
                    )
                elif reason:
                    rejected[key] = reason

            ean = (medicine.codigo_barras or "").strip()
            source_records = state.get("indiana_by_ean", {}).get(ean, []) if ean else []
            if not ean:
                possible = state.get("indiana_by_name", {}).get(
                    normalized(medicine.name_search), []
                )
                candidate_eans = {str(rec["item"].get("ean") or "") for rec in possible}
                if len(possible) == 1 or (
                    len(candidate_eans) == 1 and "" not in candidate_eans
                ):
                    source_records = possible
            for record in source_records:
                item = record["item"]
                source_ean = str(item.get("ean") or "").strip()
                expected_ean = ean or source_ean or None
                if ean and source_ean != ean:
                    continue
                if not ean and normalized(str(record.get("name") or "")) != normalized(
                    medicine.name_search
                ):
                    continue
                image_url = select_vtex_item_image(
                    item, expected_ean=expected_ean, expected_sku=record["sku"]
                )
                if image_url:
                    candidates.append(
                        (
                            image_url,
                            "Indiana",
                            f"IND{record['sku']}",
                            expected_ean,
                            "ean" if expected_ean else "sku",
                        )
                    )
            targets.append(
                {
                    "key": key,
                    "medicine": medicine,
                    "ean": ean,
                    "candidates": candidates,
                    "indiana_skus": sorted(indiana_skus),
                }
            )

        semaphore = asyncio.Semaphore(10)

        async def resolve(target: dict) -> tuple[dict, tuple | None, str | None]:
            last_reason = rejected.get(target["key"])
            for image_url, source, sku, ean, match in target["candidates"]:
                reason = image_rejection_reason(image_url)
                if reason:
                    last_reason = reason
                    continue
                async with semaphore:
                    check = await verify_image_url(image_url, timeout_seconds=5)
                if check.ok:
                    return (
                        target,
                        (image_url, source or check.source, sku, ean, match),
                        None,
                    )
                last_reason = check.reason

            for sku in target["indiana_skus"]:
                record = await lookup_indiana_sku(sku, state)
                if not record:
                    continue
                source_ean = str(record["item"].get("ean") or "").strip()
                if target["ean"] and source_ean != target["ean"]:
                    last_reason = "EAN mismatch in exact SKU lookup"
                    continue
                if not target["ean"] and normalized(
                    str(record.get("name") or "")
                ) != normalized(target["medicine"].name_search):
                    last_reason = "Full product name mismatch in exact SKU lookup"
                    continue
                image_url = select_vtex_item_image(
                    record["item"],
                    expected_ean=target["ean"] or source_ean or None,
                    expected_sku=sku,
                )
                if not image_url:
                    continue
                async with semaphore:
                    check = await verify_image_url(image_url, timeout_seconds=5)
                if check.ok:
                    return (
                        target,
                        (
                            image_url,
                            "Indiana",
                            f"IND{sku}",
                            target["ean"] or source_ean or None,
                            "ean" if target["ean"] or source_ean else "sku",
                        ),
                        None,
                    )
                last_reason = check.reason
            return target, None, last_reason

        source_complete = bool(state.get("indiana_complete")) or no_discovery
        for offset in range(0, len(targets), 40):
            batch = targets[offset : offset + 40]
            results = await asyncio.gather(*(resolve(target) for target in batch))
            for target, chosen, reason in results:
                medicine = target["medicine"]
                key = target["key"]
                if chosen:
                    url, source, sku, ean, match = chosen
                    medicine.imagem_url = url
                    medicine.imagem_fonte = source
                    medicine.imagem_sku_origem = sku
                    medicine.imagem_ean = ean
                    medicine.imagem_match = match
                    medicine.imagem_status = "verificada"
                    medicine.imagem_verificada_em = datetime.now(timezone.utc)
                    medicine.imagem_motivo_rejeicao = None
                    recovered[key] = {"source": source, "match": match}
                    rejected.pop(key, None)
                    processed.add(key)
                else:
                    recovered.pop(key, None)
                    medicine.imagem_status = (
                        "sem_imagem" if source_complete else "pendente"
                    )
                    if reason:
                        rejected[key] = reason
                    medicine.imagem_motivo_rejeicao = reason or (
                        "Indiana public search did not cover the complete catalog."
                        if not source_complete
                        else (
                            "No exact product image was available "
                            "in the consulted sources."
                        )
                    )
                    if source_complete:
                        processed.add(key)
            db.commit()
            state.update(
                processed_ids=sorted(processed, key=int),
                recovered=recovered,
                rejected=rejected,
            )
            save_state(state)
            print(
                f"Audited {min(offset + len(batch), len(targets))}/{len(targets)}; "
                f"verified {len(recovered)}; unresolved {len(rejected)}",
                flush=True,
            )

        counts = {
            "catalog_total": db.query(CatalogoBase).count(),
            "baseline": state.get("baseline", {}),
            "indiana_source_scan_complete": source_complete,
            "indiana_source_error": state.get("discovery_error"),
            "indiana_source_http_status": state.get("discovery_http_status"),
            "verified": db.query(CatalogoBase)
            .filter(CatalogoBase.imagem_status == "verificada")
            .count(),
            "unresolved": db.query(CatalogoBase)
            .filter(CatalogoBase.imagem_status != "verificada")
            .count(),
            "recovered_by_source": {},
            "remaining": [
                {
                    "id": item.id,
                    "name": item.name_search,
                    "ean": item.codigo_barras,
                    "reason": item.imagem_motivo_rejeicao,
                }
                for item in db.query(CatalogoBase)
                .filter(CatalogoBase.imagem_status != "verificada")
                .order_by(CatalogoBase.id)
                .all()
            ],
        }
        for source, count in (
            db.query(CatalogoBase.imagem_fonte, func.count())
            .filter(CatalogoBase.imagem_status == "verificada")
            .group_by(CatalogoBase.imagem_fonte)
            .all()
        ):
            counts["recovered_by_source"][source or "unknown"] = count
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {key: value for key, value in counts.items() if key != "remaining"},
                ensure_ascii=False,
            ),
            flush=True,
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-discovery", action="store_true")
    parser.add_argument("--recheck-verified", action="store_true")
    parser.add_argument(
        "--retry-discovery",
        action="store_true",
        help="Retry the paginated source scan from its saved offset after a failure.",
    )
    args = parser.parse_args()
    asyncio.run(
        main(
            args.limit,
            args.no_discovery,
            args.recheck_verified,
            args.retry_discovery,
        )
    )
