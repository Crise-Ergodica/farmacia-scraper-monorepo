"""Audit catalog identity and recover only GTINs from exact official offer pages."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CatalogoBase, HistoricoPreco, OfertaFarmacia
from app.models.usuario import usuario_medicamento_favorito
from scripts.processar_imagens import normalized

REPORT = Path(__file__).resolve().parents[1] / "reports" / "catalog-integrity.json"
SIMULATION = REPORT.with_name("catalog-consolidation-simulation.json")
ARAUJO_PAGE = re.compile(r"https://www\.araujo\.com\.br/[^?#]+/(\d+)\.html$")


def valid_gtin(code: str) -> bool:
    if not re.fullmatch(r"\d{13}", code):
        return False
    digits = [int(value) for value in code]
    total = sum(
        value * (3 if index % 2 else 1) for index, value in enumerate(digits[:12])
    )
    return (10 - total % 10) % 10 == digits[12]


def product_data(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string or tag.get_text())
        except (TypeError, ValueError):
            continue
        products = data if isinstance(data, list) else [data]
        for product in products:
            if isinstance(product, dict) and product.get("@type") == "Product":
                return product
    return None


def main(*, apply_eans: bool) -> None:
    previous_report = (
        json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    )
    db = SessionLocal()
    try:
        catalog = (
            db.execute(select(CatalogoBase).order_by(CatalogoBase.id)).scalars().all()
        )
        offers = db.execute(select(OfertaFarmacia)).scalars().all()
        history = Counter(db.execute(select(HistoricoPreco.medicamento_id)).scalars())
        favorites = Counter(
            db.execute(select(usuario_medicamento_favorito.c.medicamento_id)).scalars()
        )
        offers_by_catalog = defaultdict(list)
        by_sku = defaultdict(set)
        by_url = defaultdict(set)
        for offer in offers:
            offers_by_catalog[offer.catalogo_id].append(offer)
            by_sku[offer.sku_interno].add(offer.catalogo_id)
            by_url[offer.url_origem].add(offer.catalogo_id)
        ean_owner = {
            item.codigo_barras: item.id for item in catalog if item.codigo_barras
        }
        name_groups = defaultdict(list)
        for item in catalog:
            if not item.codigo_barras:
                name_groups[normalized(item.name_search)].append(item)

        identity_checks = []
        recovered_eans = []
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            for item in catalog:
                if item.codigo_barras:
                    continue
                for offer in offers_by_catalog[item.id]:
                    url = offer.url_origem or ""
                    match = ARAUJO_PAGE.fullmatch(url)
                    if not match or offer.sku_interno != f"ARJ{match.group(1)}":
                        continue
                    result = {
                        "catalog_id": item.id,
                        "offer_id": offer.id,
                        "sku": offer.sku_interno,
                        "official_url": url,
                    }
                    try:
                        response = client.get(
                            url, headers={"User-Agent": "Mozilla/5.0"}
                        )
                        result["http_status"] = response.status_code
                        if (
                            response.status_code != 200
                            or len(response.content) > 3_000_000
                        ):
                            result["status"] = "page_unavailable"
                        else:
                            product = product_data(response.text)
                            gtin = str((product or {}).get("gtin13") or "").strip()
                            page_name = str((product or {}).get("name") or "")
                            result.update(gtin=gtin, page_name=page_name)
                            if not product or str(product.get("sku")) != match.group(1):
                                result["status"] = "sku_mismatch_or_missing"
                            elif normalized(page_name) != normalized(item.name_search):
                                result["status"] = "presentation_name_mismatch"
                            elif not valid_gtin(gtin):
                                result["status"] = "gtin_missing_or_invalid"
                            elif gtin in ean_owner:
                                result["status"] = "gtin_already_on_another_catalog_row"
                                result["existing_catalog_id"] = ean_owner[gtin]
                            else:
                                result["status"] = "exact_official_gtin"
                                if apply_eans:
                                    item.codigo_barras = gtin
                                    ean_owner[gtin] = item.id
                                    result["status"] = "gtin_saved"
                                    recovered_eans.append(result)
                    except httpx.HTTPError as exc:
                        result.update(
                            status="source_unavailable", error=type(exc).__name__
                        )
                    identity_checks.append(result)

        if apply_eans and recovered_eans:
            db.commit()

        recovered_eans = (
            list(previous_report.get("eans_recovered", [])) + recovered_eans
        )
        conflicts = []
        for check in identity_checks:
            if check["status"] != "gtin_already_on_another_catalog_row":
                continue
            source = db.get(CatalogoBase, check["catalog_id"])
            existing = db.get(CatalogoBase, check["existing_catalog_id"])
            conflicts.append(
                {
                    "source_catalog_id": source.id,
                    "existing_ean_catalog_id": existing.id,
                    "official_gtin": check["gtin"],
                    "official_sku": check["sku"],
                    "official_url": check["official_url"],
                    "source_name": source.name_search,
                    "ean_row_name": existing.name_search,
                    "source_relationships": {
                        "offers": len(offers_by_catalog[source.id]),
                        "price_history": history[source.id],
                        "favorites": favorites[source.id],
                    },
                    "target_relationships": {
                        "offers": len(offers_by_catalog[existing.id]),
                        "price_history": history[existing.id],
                        "favorites": favorites[existing.id],
                    },
                    "classification": "official_gtin_conflict_review_required",
                    "dry_run_only": True,
                    "requires_specific_approval": True,
                }
            )

        possible_duplicates = []
        for rows in name_groups.values():
            if len(rows) < 2:
                continue
            possible_duplicates.append(
                {
                    "name": rows[0].name_search,
                    "classification": "possible_duplicate_name_only",
                    "rows": [
                        {
                            "id": row.id,
                            "ean": row.codigo_barras,
                            "offer_skus": [
                                o.sku_interno for o in offers_by_catalog[row.id]
                            ],
                            "offer_urls": [
                                o.url_origem for o in offers_by_catalog[row.id]
                            ],
                            "price_history_count": history[row.id],
                            "favorite_count": favorites[row.id],
                        }
                        for row in rows
                    ],
                }
            )
        report = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "catalog_total": len(catalog),
            "verified_images": sum(i.imagem_status == "verificada" for i in catalog),
            "pending_images": sum(i.imagem_status != "verificada" for i in catalog),
            "without_ean": sum(not i.codigo_barras for i in catalog),
            "without_offers": sum(not offers_by_catalog[i.id] for i in catalog),
            "without_ean_or_offers": sum(
                not i.codigo_barras and not offers_by_catalog[i.id] for i in catalog
            ),
            "confirmed_duplicate_sku_groups": [
                {"sku": sku, "catalog_ids": sorted(ids)}
                for sku, ids in by_sku.items()
                if len(ids) > 1
            ],
            "confirmed_duplicate_url_groups": [
                {"url": url, "catalog_ids": sorted(ids)}
                for url, ids in by_url.items()
                if len(ids) > 1
            ],
            "possible_duplicate_name_groups": possible_duplicates,
            "confirmed_unique_products": None,
            "unique_product_count_reason": (
                "Rows without EAN or offer identifier cannot be merged or counted "
                "as confirmed unique products from a matching title alone."
            ),
            "ean_source_checks": identity_checks,
            "eans_recovered": recovered_eans,
            "official_gtin_conflicts": len(conflicts),
            "consolidation_simulation_file": SIMULATION.name,
            "consolidation_reason": (
                "Official GTIN conflicts require individual identity and relationship "
                "review before any merge or reassignment."
            ),
        }
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        SIMULATION.write_text(
            json.dumps(
                {
                    "proposal_count": len(conflicts),
                    "proposed": conflicts,
                    "no_changes_applied": True,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        REPORT.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    key: value
                    for key, value in report.items()
                    if key
                    not in {
                        "possible_duplicate_name_groups",
                        "ean_source_checks",
                        "eans_recovered",
                    }
                },
                ensure_ascii=False,
            )
        )
        print("possible_duplicate_groups", len(possible_duplicates))
        print("ean_source_results", dict(Counter(r["status"] for r in identity_checks)))
        print("eans_recovered", len(recovered_eans))
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-eans", action="store_true")
    main(apply_eans=parser.parse_args().apply_eans)
