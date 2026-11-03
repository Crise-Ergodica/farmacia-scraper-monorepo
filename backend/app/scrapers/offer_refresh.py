"""Bounded, resumable price observations from existing official offer URLs.

This job never discovers new products. A source response must identify the
same SKU and, when available, the same catalog EAN before it can change data.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import SessionLocal
from app.models.farmacia import Farmacia
from app.models.oferta_farmacia import OfertaFarmacia
from app.services.preco_observacoes import registrar_observacao_preco

SOURCE_CNPJ = {"indiana": "00000000000100", "araujo": "17256512000116"}
STATE_DIR = Path(os.getenv("OFFER_REFRESH_STATE_DIR", "data/offer_refresh"))
USER_AGENT = "Preco Bao catalog audit/1.0"


class SourceUnavailable(Exception):
    """A source could not be checked; this is not evidence of a missing price."""


class IdentityMismatch(Exception):
    """The source response does not identify this exact offer."""


def _price(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise SourceUnavailable("invalid_source_price") from error
    if not result.is_finite() or result <= 0:
        raise SourceUnavailable("invalid_source_price")
    return result


def _identity(offer: OfertaFarmacia, sku: str, ean: str | None) -> None:
    expected_sku = offer.sku_interno.removeprefix("IND").removeprefix("ARJ")
    if sku != expected_sku:
        raise IdentityMismatch("sku_mismatch")
    expected_ean = offer.produto_catalogo.codigo_barras
    if expected_ean and ean and expected_ean != ean:
        raise IdentityMismatch("ean_mismatch")


def parse_indiana(offer: OfertaFarmacia, payload: object) -> tuple[Decimal, bool]:
    if not isinstance(payload, list) or len(payload) != 1:
        raise SourceUnavailable("product_not_found_or_ambiguous")
    product = payload[0]
    if not isinstance(product, dict):
        raise SourceUnavailable("malformed_catalog_response")
    if product.get("link") != offer.url_origem:
        raise IdentityMismatch("product_url_mismatch")
    items = [
        item
        for item in product.get("items", [])
        if str(item.get("itemId")) == offer.sku_interno.removeprefix("IND")
    ]
    if len(items) != 1:
        raise IdentityMismatch("sku_missing_or_ambiguous")
    item = items[0]
    if not isinstance(item, dict):
        raise SourceUnavailable("malformed_catalog_response")
    _identity(offer, str(item["itemId"]), str(item.get("ean") or "") or None)
    sellers = [
        seller for seller in item.get("sellers", []) if seller.get("sellerDefault")
    ]
    if len(sellers) != 1:
        raise SourceUnavailable("official_seller_missing_or_ambiguous")
    commercial = sellers[0].get("commertialOffer") or {}
    return _price(commercial.get("Price")), bool(commercial.get("IsAvailable"))


def parse_araujo(offer: OfertaFarmacia, html: str) -> tuple[Decimal, bool]:
    products = []
    for script in BeautifulSoup(html, "html.parser").find_all(
        "script", type="application/ld+json"
    ):
        try:
            data = json.loads(script.string or script.text)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            products.append(data)
    if len(products) != 1:
        raise SourceUnavailable("structured_product_missing_or_ambiguous")
    product = products[0]
    _identity(offer, str(product.get("sku")), str(product.get("gtin13") or "") or None)
    sale = product.get("offers") or {}
    if not isinstance(sale, dict):
        raise SourceUnavailable("structured_offer_missing_or_ambiguous")
    if sale.get("url") != offer.url_origem:
        raise IdentityMismatch("product_url_mismatch")
    if sale.get("priceCurrency") != "BRL":
        raise SourceUnavailable("currency_not_brl")
    availability = sale.get("availability")
    if availability not in {
        "https://schema.org/InStock",
        "https://schema.org/OutOfStock",
    }:
        raise SourceUnavailable("availability_unknown")
    return _price(sale.get("price")), availability.endswith("/InStock")


def _source_url(offer: OfertaFarmacia, source: str) -> str:
    parsed = urlparse(offer.url_origem)
    expected_host = {
        "indiana": "www.farmaciaindiana.com.br",
        "araujo": "www.araujo.com.br",
    }[source]
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise IdentityMismatch("untrusted_product_url")
    if source == "indiana":
        sku = offer.sku_interno.removeprefix("IND")
        if not sku.isdigit():
            raise IdentityMismatch("invalid_sku")
        return (
            "https://www.farmaciaindiana.com.br/api/catalog_system/pub/"
            f"products/search/?fq=skuId:{sku}"
        )
    return offer.url_origem


def fetch_observation(
    client: httpx.Client, offer: OfertaFarmacia, source: str
) -> tuple[Decimal, bool]:
    url = _source_url(offer, source)
    try:
        response = client.get(url)
    except httpx.HTTPError as error:
        raise SourceUnavailable(type(error).__name__) from error
    if response.status_code != 200:
        raise SourceUnavailable(f"http_{response.status_code}")
    if source == "indiana":
        try:
            return parse_indiana(offer, response.json())
        except (ValueError, KeyError, TypeError) as error:
            raise SourceUnavailable("malformed_catalog_response") from error
    return parse_araujo(offer, response.text)


def record_observation(
    db: Session, offer: OfertaFarmacia, source: str, price: Decimal, available: bool
) -> bool:
    previous = offer.preco
    offer.disponivel = available
    event = registrar_observacao_preco(
        offer,
        preco=price,
        observado_em=datetime.now(UTC),
        origem=source.title(),
        farmacia_id=offer.farmacia_id,
        medicamento_id=offer.catalogo_id,
        preco_anterior=previous,
    )
    if event is not None:
        db.add(event)
    db.commit()
    return event is not None


def _state_path(source: str) -> Path:
    return STATE_DIR / f"{source}.json"


def _read_cursor(source: str) -> int:
    try:
        return int(
            json.loads(_state_path(source).read_text(encoding="utf-8"))["cursor"]
        )
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def _write_state(source: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{source}-", dir=STATE_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, _state_path(source))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def _run_lock():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "refresh.lock").open("a+b") as stream:
        try:
            if os.name == "nt":
                import msvcrt

                if not stream.read(1):
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("Offer refresh already running") from error
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def refresh(source: str, limit: int, delay: float = 1.0) -> dict:
    if source not in SOURCE_CNPJ or limit <= 0 or delay < 0:
        raise ValueError("Invalid refresh source, limit or delay")
    stats = {
        "source": source,
        "checked": 0,
        "events": 0,
        "unchanged": 0,
        "unavailable": 0,
        "mismatch": 0,
        "cursor": 0,
        "errors": [],
    }
    with (
        _run_lock(),
        SessionLocal() as db,
        httpx.Client(
            timeout=20,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html, application/json"},
        ) as client,
    ):
        pharmacy_id = db.scalar(
            select(Farmacia.id).where(Farmacia.cnpj == SOURCE_CNPJ[source])
        )
        if pharmacy_id is None:
            raise RuntimeError(f"Pharmacy not found for {source}")
        cursor = _read_cursor(source)
        stats["cursor"] = cursor
        offers = db.scalars(
            select(OfertaFarmacia)
            .options(joinedload(OfertaFarmacia.produto_catalogo))
            .where(
                OfertaFarmacia.farmacia_id == pharmacy_id,
                OfertaFarmacia.id > cursor,
            )
            .order_by(OfertaFarmacia.id)
            .limit(limit)
        ).all()
        if not offers:
            cursor = 0
            offers = db.scalars(
                select(OfertaFarmacia)
                .options(joinedload(OfertaFarmacia.produto_catalogo))
                .where(OfertaFarmacia.farmacia_id == pharmacy_id)
                .order_by(OfertaFarmacia.id)
                .limit(limit)
            ).all()
        for offer in offers:
            try:
                price, available = fetch_observation(client, offer, source)
                if record_observation(db, offer, source, price, available):
                    stats["events"] += 1
                else:
                    stats["unchanged"] += 1
            except IdentityMismatch as error:
                db.rollback()
                stats["mismatch"] += 1
                stats["errors"].append({"offer_id": offer.id, "reason": str(error)})
            except SourceUnavailable as error:
                db.rollback()
                stats["unavailable"] += 1
                stats["errors"].append({"offer_id": offer.id, "reason": str(error)})
                if str(error) in {"http_403", "http_429"}:
                    stats["stop_reason"] = str(error)
                    _write_state(
                        source, {**stats, "updated_at": datetime.now(UTC).isoformat()}
                    )
                    break
            stats["checked"] += 1
            stats["cursor"] = offer.id
            _write_state(source, {**stats, "updated_at": datetime.now(UTC).isoformat()})
            if delay:
                time.sleep(delay)
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=SOURCE_CNPJ)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()
    print(json.dumps(refresh(args.source, args.limit, args.delay), ensure_ascii=False))
