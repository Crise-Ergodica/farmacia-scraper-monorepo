"""Prepare/test an isolated PostgreSQL image-reference restore.

The destination database name must end with ``image_restore_test`` and be empty.
Run Alembic against it before invoking this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine.url import make_url

from app.core.database import SessionLocal
from app.main import app
from app.models import CatalogoBase, Farmacia, OfertaFarmacia
from app.services.image_reference_portability import import_image_references
from app.services.imagens import catalog_image_matches_record


def same_url(first: str | None, second: str | None) -> bool:
    if not first or not second:
        return False
    left, right = urlsplit(first), urlsplit(second)
    return (
        left.scheme.casefold() == right.scheme.casefold()
        and (left.hostname or "").casefold() == (right.hostname or "").casefold()
        and unquote(left.path) == unquote(right.path)
        and sorted(parse_qsl(left.query, keep_blank_values=True))
        == sorted(parse_qsl(right.query, keep_blank_values=True))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-validation", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url or not make_url(database_url).database.endswith(
        "image_restore_test"
    ):
        raise SystemExit(
            "Proteção: DATABASE_URL precisa apontar para *_image_restore_test."
        )
    document = json.loads(args.input.read_text(encoding="utf-8"))
    external_audit = json.loads(args.source_validation.read_text(encoding="utf-8"))
    source_results = {
        item["url"]: item for item in external_audit.get("source_results", [])
    }
    exported_urls = {item["image"]["url"] for item in document.get("records", [])}
    external_urls_valid = exported_urls == set(source_results) and all(
        source_results[url].get("ok") for url in exported_urls
    )

    with SessionLocal() as db:
        catalog_count = db.scalar(select(func.count()).select_from(CatalogoBase)) or 0
        pharmacy_count = db.scalar(select(func.count()).select_from(Farmacia)) or 0
        offer_count = db.scalar(select(func.count()).select_from(OfertaFarmacia)) or 0
        if catalog_count or pharmacy_count or offer_count:
            raise SystemExit(
                "Proteção: banco de teste não está vazio; importação cancelada."
            )

        products: dict[int, CatalogoBase] = {}
        pharmacies: dict[str, Farmacia] = {}
        # Reverse insertion order intentionally makes source/local IDs diverge.
        for record in reversed(document["records"]):
            identity = record.get("identity") or {}
            product = CatalogoBase(
                codigo_barras=identity.get("ean"),
                name_search=identity.get("name") or "Produto sem nome no manifesto",
                principio_ativo="Não informado",
                laboratorio="Não informado",
                exige_receita=False,
                categorias=[],
            )
            db.add(product)
            products[record["source_catalog_id"]] = product
        db.flush()

        unique_offers: set[tuple[str, str]] = set()
        for record in document["records"]:
            product = products[record["source_catalog_id"]]
            identity = record.get("identity") or {}
            for offer in identity.get("offers") or []:
                pharmacy_name = offer.get("pharmacy")
                sku = offer.get("sku")
                product_url = offer.get("product_url")
                if not pharmacy_name or not sku or not product_url:
                    continue
                offer_key = (pharmacy_name, product_url)
                if offer_key in unique_offers:
                    continue
                unique_offers.add(offer_key)
                pharmacy = pharmacies.get(pharmacy_name)
                if pharmacy is None:
                    pharmacy = Farmacia(
                        cnpj=f"90000000{len(pharmacies) + 1:06d}",
                        razao_social=f"Fixture {pharmacy_name}",
                        nome_fantasia=pharmacy_name,
                        telefone=None,
                        endereco_completo="Fixture isolado de restauração",
                    )
                    db.add(pharmacy)
                    db.flush()
                    pharmacies[pharmacy_name] = pharmacy
                db.add(
                    OfertaFarmacia(
                        sku_interno=sku,
                        preco=Decimal("0.00"),
                        quantidade_estoque=0,
                        disponivel=False,
                        url_origem=product_url,
                        imagem_url=offer.get("offer_image_url"),
                        farmacia=pharmacy,
                        produto_catalogo=product,
                    )
                )
        db.commit()
        seeded_catalog_count = (
            db.scalar(select(func.count()).select_from(CatalogoBase)) or 0
        )

        first_import = import_image_references(db, document)
        second_import = import_image_references(db, document)
        products_after = db.execute(select(CatalogoBase)).scalars().all()
        associated = sum(bool(product.imagem_url) for product in products_after)
        eligible = sum(
            catalog_image_matches_record(product) for product in products_after
        )
        reference_urls = {
            product.imagem_url for product in products_after if product.imagem_url
        }
        referenced_products = [
            product for product in products_after if product.imagem_url
        ]
        route_ok = 0
        route_failed: list[dict[str, object]] = []
        with TestClient(app) as client:
            for product in referenced_products:
                response = client.get(
                    f"/catalogo/medicamentos/{product.id}/imagem",
                    follow_redirects=False,
                )
                expected = product.imagem_url
                if response.status_code == 302 and same_url(
                    response.headers.get("location"), expected
                ):
                    route_ok += 1
                else:
                    route_failed.append(
                        {
                            "catalog_id": product.id,
                            "status": response.status_code,
                            "reason": response.text[:200],
                        }
                    )

    report = {
        "database_suffix_guard": "image_restore_test",
        "source_export_file": args.input.name,
        "migrations_prepared_before_seed": True,
        "catalog_count": seeded_catalog_count,
        "source_export_count": document.get("record_count"),
        "reference_count": associated,
        "unmatched_catalog_products": seeded_catalog_count - associated,
        "identity_eligible_count": eligible,
        "unique_reference_urls": len(reference_urls),
        "unique_source_urls_confirmed_by_existing_full_audit": external_urls_valid,
        "source_audit_url_count": len(source_results),
        "first_import": first_import,
        "second_import": second_import,
        "api_image_routes_ok": route_ok,
        "api_image_routes_failed": route_failed,
        "api_image_route_count": len(referenced_products),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key != "first_import" and key != "second_import"
            }
        )
    )
    success = (
        seeded_catalog_count == document.get("record_count")
        and associated
        == len(document.get("records", [])) - first_import["unmatched_count"]
        and eligible == associated
        and external_urls_valid
        and route_ok == associated
        and not route_failed
        and first_import["conflict_count"] == 0
        and second_import["already_present"] == associated
    )
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
