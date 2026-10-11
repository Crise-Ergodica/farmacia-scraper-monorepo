"""Resumable catalog image audit using exact pharmacy SKU/EAN identity."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import CatalogoBase, Farmacia, OfertaFarmacia
from app.services.imagens import (
    embedded_eans,
    image_rejection_reason,
    select_araujo_product_image,
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


def negative_cache_is_fresh(state: dict, source: str, key: str) -> bool:
    """Retry absent source images after a week, but keep immediate reruns cheap."""
    checked = state.setdefault("negative_checked_at", {})
    cache_key = f"{source}:{key}"
    today = datetime.now(timezone.utc).date()
    if cache_key not in checked:
        checked[cache_key] = today.isoformat()
        return True
    try:
        return (today - date.fromisoformat(checked[cache_key])).days < 7
    except ValueError:
        return False


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
        if cache[sku] is not None or negative_cache_is_fresh(state, "indiana", sku):
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
        if exact is None:
            state.setdefault("negative_checked_at", {})[f"indiana:{sku}"] = (
                datetime.now(timezone.utc).date().isoformat()
            )
        await asyncio.sleep(0.25)
        return exact
    except (httpx.HTTPError, ValueError) as exc:
        state.setdefault("indiana_sku_errors", {})[sku] = type(exc).__name__
        return None


async def lookup_indiana_ean(ean: str, state: dict) -> dict | None:
    """Query an exact EAN beyond the public search pagination ceiling."""
    cache: dict[str, dict | None] = state.setdefault("indiana_by_ean_lookup", {})
    if ean in cache:
        if cache[ean] is not None or negative_cache_is_fresh(state, "indiana_ean", ean):
            return cache[ean]
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            response = await client.get(
                SKU_API_URL, params={"fq": f"alternateIds_Ean:{ean}"}
            )
            response.raise_for_status()
            if len(response.content) > 3_000_000:
                raise ValueError("EAN response too large")
            products = response.json()
            if not isinstance(products, list):
                raise ValueError("Unexpected EAN response")
        exact = next(
            (
                {
                    "item": item,
                    "name": product.get("productName"),
                    "sku": str(item.get("itemId") or ""),
                    "link": product.get("link"),
                }
                for product in products
                for item in product.get("items") or []
                if str(item.get("ean") or "").strip() == ean
                and select_vtex_item_image(item, expected_ean=ean)
            ),
            None,
        )
        cache[ean] = exact
        if exact is None:
            state.setdefault("negative_checked_at", {})[f"indiana_ean:{ean}"] = (
                datetime.now(timezone.utc).date().isoformat()
            )
        await asyncio.sleep(0.25)
        return exact
    except (httpx.HTTPError, ValueError) as exc:
        state.setdefault("indiana_ean_errors", {})[ean] = type(exc).__name__
        return None


async def lookup_araujo_image(offer: OfertaFarmacia, state: dict) -> str | None:
    """Read the exact product page when its listing used a generic thumbnail."""
    sku = offer.sku_interno or ""
    cache = state.setdefault("araujo_by_sku", {})
    if sku in cache:
        if cache[sku] is not None or negative_cache_is_fresh(state, "araujo_sku", sku):
            return cache[sku]
    url = offer.url_origem or ""
    if not re.fullmatch(r"https://www\.araujo\.com\.br/[^?#]+/\d+\.html", url):
        state.setdefault("araujo_errors", {})[sku] = "Invalid product URL"
        return None
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        if len(response.content) > 3_000_000:
            state.setdefault("araujo_errors", {})[sku] = "Product page too large"
            return None
        image = select_araujo_product_image(
            response.text, sku=sku, ean=None, product_url=url
        )
        cache[sku] = image
        if not image:
            state.setdefault("araujo_errors", {})[sku] = "No exact SKU image on page"
            state.setdefault("negative_checked_at", {})[f"araujo_sku:{sku}"] = (
                datetime.now(timezone.utc).date().isoformat()
            )
        await asyncio.sleep(0.25)
        return image
    except (httpx.HTTPError, ValueError) as exc:
        state.setdefault("araujo_errors", {})[sku] = type(exc).__name__
        return None


async def lookup_araujo_ean(ean: str, state: dict) -> tuple[str, str] | None:
    """Find an exact EAN photograph on Araújo without creating a commercial offer."""
    cache = state.setdefault("araujo_by_ean", {})
    if ean in cache:
        cached = cache[ean]
        if cached or negative_cache_is_fresh(state, "araujo_ean", ean):
            return tuple(cached) if cached else None
    search_url = "https://www.araujo.com.br/busca"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.get(
                search_url, params={"q": ean}, headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            if len(response.content) > 3_000_000:
                raise ValueError("Search page too large")
            soup = BeautifulSoup(response.text, "html.parser")
            product_urls = []
            for link in soup.select('a[href]'):
                url = urljoin(search_url, str(link.get("href") or ""))
                if re.fullmatch(
                    r"https://www\.araujo\.com\.br/[^?#]+/\d+\.html", url
                ) and url not in product_urls:
                    product_urls.append(url)
            for product_url in product_urls[:5]:
                page = await client.get(
                    product_url, headers={"User-Agent": "Mozilla/5.0"}
                )
                page.raise_for_status()
                if len(page.content) > 3_000_000:
                    continue
                sku = re.search(r"/(\d+)\.html$", product_url).group(1)
                image = select_araujo_product_image(
                    page.text,
                    sku=f"ARJ{sku}",
                    ean=ean,
                    product_url=product_url,
                )
                if image and ean in embedded_eans(image):
                    cache[ean] = [image, f"ARJ{sku}"]
                    await asyncio.sleep(0.4)
                    return image, f"ARJ{sku}"
        cache[ean] = None
        state.setdefault("negative_checked_at", {})[f"araujo_ean:{ean}"] = (
            datetime.now(timezone.utc).date().isoformat()
        )
        state.setdefault("araujo_ean_errors", {})[ean] = "No exact EAN photo"
    except (httpx.HTTPError, ValueError) as exc:
        state.setdefault("araujo_ean_errors", {})[ean] = type(exc).__name__
    return None


async def main(
    limit: int | None = None,
    no_discovery: bool = False,
    recheck_verified: bool = False,
    retry_discovery: bool = False,
    recheck_invalid: bool = False,
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

    processed: set[str] = set(state.get("processed_ids", []))
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
            if recheck_invalid:
                image_eans = embedded_eans(medicine.imagem_url or "")
                if medicine.imagem_status != "verificada" or not (
                    image_rejection_reason(medicine.imagem_url or "")
                    or (
                        medicine.codigo_barras
                        and image_eans
                        and medicine.codigo_barras not in image_eans
                    )
                ):
                    continue
            elif recheck_verified and medicine.imagem_status != "verificada":
                continue
            elif not recheck_verified and (
                key in processed or medicine.imagem_status == "verificada"
            ):
                continue
            candidates = []
            indiana_skus = set()
            araujo_offers = []
            if medicine.imagem_url:
                file_eans = embedded_eans(medicine.imagem_url)
                if (
                    medicine.codigo_barras
                    and file_eans
                    and medicine.codigo_barras not in file_eans
                ):
                    rejected[key] = "O EAN no arquivo diverge do medicamento."
                else:
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
                if (offer.sku_interno or "").startswith("ARJ"):
                    araujo_offers.append(offer)
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
                    "araujo_offers": araujo_offers,
                }
            )

        semaphore = asyncio.Semaphore(10)
        search_semaphore = asyncio.Semaphore(3)

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

            for offer in target["araujo_offers"]:
                async with semaphore:
                    image_url = await lookup_araujo_image(offer, state)
                if not image_url:
                    last_reason = state.get("araujo_errors", {}).get(
                        offer.sku_interno, last_reason
                    )
                    continue
                valid, match, reason = validate_image_association(
                    image_url=image_url,
                    pharmacy_name="Araujo",
                    sku=offer.sku_interno,
                    ean=target["ean"],
                    product_url=offer.url_origem,
                )
                if not valid:
                    last_reason = reason
                    continue
                async with semaphore:
                    check = await verify_image_url(image_url, timeout_seconds=8)
                if check.ok:
                    offer.imagem_url = image_url
                    return (
                        target,
                        (image_url, "Araujo", offer.sku_interno, target["ean"], match),
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
            if target["ean"] and target["ean"] not in state.get("indiana_by_ean", {}):
                async with search_semaphore:
                    record = await lookup_indiana_ean(target["ean"], state)
                if record:
                    image_url = select_vtex_item_image(
                        record["item"],
                        expected_ean=target["ean"],
                        expected_sku=record["sku"],
                    )
                    if image_url:
                        async with semaphore:
                            check = await verify_image_url(image_url, timeout_seconds=5)
                        if check.ok:
                            return (
                                target,
                                (
                                    image_url,
                                    "Indiana",
                                    f"IND{record['sku']}",
                                    target["ean"],
                                    "ean",
                                ),
                                None,
                            )
                        last_reason = check.reason

            if target["ean"] and len(target["ean"]) == 13:
                async with search_semaphore:
                    found = await lookup_araujo_ean(target["ean"], state)
                if found:
                    image_url, sku = found
                    async with semaphore:
                        check = await verify_image_url(image_url, timeout_seconds=8)
                    if check.ok:
                        return (
                            target,
                            (image_url, "Araujo", sku, target["ean"], "ean"),
                            None,
                        )
                    last_reason = check.reason
                else:
                    last_reason = state.get("araujo_ean_errors", {}).get(
                        target["ean"], last_reason
                    )
            return target, None, last_reason

        source_complete = bool(state.get("indiana_complete"))
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
        "--recheck-invalid",
        action="store_true",
        help="Reprocess verified images rejected by local identity or URL checks.",
    )
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
            args.recheck_invalid,
        )
    )
