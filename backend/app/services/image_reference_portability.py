"""Versioned, privacy-safe export/import for persistent catalog image references."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.models.oferta_farmacia import OfertaFarmacia
from app.services.imagens import (
    catalog_image_matches_record,
    gtin_matches,
    image_delivery_rejection_reason,
    source_for_url,
)

SCHEMA_VERSION = 1


def export_image_references(db: Session) -> dict[str, Any]:
    """Export stable identity evidence; source database IDs are diagnostic only."""
    products = db.execute(
        select(CatalogoBase)
        .where(CatalogoBase.imagem_url.is_not(None))
        .options(
            selectinload(CatalogoBase.ofertas).selectinload(OfertaFarmacia.farmacia)
        )
        .order_by(CatalogoBase.id)
    ).scalars()
    records: list[dict[str, Any]] = []
    for product in products:
        offers = [
            {
                "pharmacy": offer.farmacia.nome_fantasia if offer.farmacia else None,
                "sku": offer.sku_interno,
                "product_url": offer.url_origem,
                "offer_image_url": offer.imagem_url,
            }
            for offer in product.ofertas
            if offer.farmacia and offer.sku_interno and offer.url_origem
        ]
        records.append(
            {
                "source_catalog_id": product.id,
                "identity": {
                    "ean": product.codigo_barras,
                    "name": product.name_search,
                    "offers": offers,
                },
                "image": {
                    "url": product.imagem_url,
                    "source": product.imagem_fonte,
                    "sku": product.imagem_sku_origem,
                    "ean": product.imagem_ean,
                    "match": product.imagem_match,
                    "status_at_export": product.imagem_status,
                    "updated_at": (
                        product.imagem_atualizada_em.isoformat()
                        if product.imagem_atualizada_em
                        else product.atualizado_em.isoformat()
                        if product.atualizado_em
                        else None
                    ),
                    "last_verified_at": (
                        product.imagem_verificada_em.isoformat()
                        if product.imagem_verificada_em
                        else None
                    ),
                    "last_checked_at": (
                        product.imagem_ultima_verificacao_em.isoformat()
                        if product.imagem_ultima_verificacao_em
                        else None
                    ),
                },
            }
        )
    return {
        "schema": "preco-bao.image-references",
        "schema_version": SCHEMA_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "record_count": len(records),
        "records": records,
    }


def import_image_references(db: Session, document: dict[str, Any]) -> dict[str, Any]:
    """Import by EAN or unique pharmacy+SKU+official product URL, never local IDs."""
    if (
        document.get("schema") != "preco-bao.image-references"
        or document.get("schema_version") != SCHEMA_VERSION
        or not isinstance(document.get("records"), list)
    ):
        raise ValueError("Arquivo de referências incompatível ou sem versão suportada.")

    counts: dict[str, Any] = {
        "input": len(document["records"]),
        "associated": 0,
        "already_present": 0,
        "conflicts": [],
        "unmatched": [],
        "invalid": [],
    }
    unmatched_records: list[tuple[str, dict[str, Any]]] = []
    for index, record in enumerate(document["records"]):
        label = f"record[{index}] source_id={record.get('source_catalog_id')}"
        identity = record.get("identity") or {}
        image = record.get("image") or {}
        url = image.get("url")
        if not isinstance(url, str) or image_delivery_rejection_reason(url):
            counts["invalid"].append(
                {"record": label, "reason": "unsafe_or_invalid_image_url"}
            )
            continue

        matched_ids: set[int] = set()
        ean = str(identity.get("ean") or "").strip()
        if ean:
            variants = {ean}
            if len(ean) == 13:
                variants.add(f"0{ean}")
            elif len(ean) == 14 and ean.startswith("0"):
                variants.add(ean[1:])
            ean_products = db.execute(
                select(CatalogoBase).where(CatalogoBase.codigo_barras.in_(variants))
            ).scalars()
            matched_ids.update(
                product.id
                for product in ean_products
                if gtin_matches(ean, product.codigo_barras)
            )

        for offer_identity in identity.get("offers") or []:
            pharmacy_name = offer_identity.get("pharmacy")
            sku = offer_identity.get("sku")
            product_url = offer_identity.get("product_url")
            if not pharmacy_name or not sku or not product_url:
                continue
            stmt = (
                select(OfertaFarmacia.catalogo_id)
                .join(Farmacia, OfertaFarmacia.farmacia_id == Farmacia.id)
                .where(
                    Farmacia.nome_fantasia == pharmacy_name,
                    OfertaFarmacia.sku_interno == sku,
                    OfertaFarmacia.url_origem == product_url,
                )
            )
            matched_ids.update(db.execute(stmt).scalars().all())

        if not matched_ids:
            unmatched_records.append((label, record))
            continue
        if len(matched_ids) != 1:
            counts["conflicts"].append(
                {
                    "record": label,
                    "reason": "stable_identifiers_resolve_to_multiple_products",
                }
            )
            continue

        product = db.get(CatalogoBase, next(iter(matched_ids)))
        if product is None:
            counts["unmatched"].append({"record": label, "ean": ean or None})
            continue
        if product.imagem_url:
            if product.imagem_url == url:
                counts["already_present"] += 1
            else:
                counts["conflicts"].append(
                    {
                        "record": label,
                        "target_catalog_id": product.id,
                        "reason": "destination_already_has_a_different_image",
                    }
                )
            continue

        product.imagem_url = url
        product.imagem_fonte = source_for_url(url)
        product.imagem_sku_origem = image.get("sku")
        product.imagem_ean = image.get("ean")
        product.imagem_match = image.get("match")
        # References are immediately deliverable; destination health is checked
        # separately and must not inherit a stale "verified" assertion.
        product.imagem_status = "pendente"
        product.imagem_atualizada_em = datetime.now(UTC)
        product.imagem_verificada_em = None
        product.imagem_ultima_verificacao_em = None
        product.imagem_falhas_consecutivas = 0
        product.imagem_ultima_falha = None
        product.imagem_motivo_rejeicao = None
        counts["associated"] += 1

    # Some legacy catalog rows have no EAN and their historical offer was removed.
    # A same-name group can still be restored safely when the entire exported group
    # agrees on exact source SKU, pharmacy, and image URL, and the destination has
    # the same group cardinality. We never use source numeric IDs for this mapping.
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in document["records"]:
        name = str((record.get("identity") or {}).get("name") or "").strip()
        if name:
            by_name[name].append(record)
    unmatched_names = {
        str((record.get("identity") or {}).get("name") or "").strip()
        for _, record in unmatched_records
    }
    resolved_group_names: set[str] = set()
    for name in unmatched_names:
        group = by_name.get(name, [])
        signatures = {
            (
                (record.get("image") or {}).get("url"),
                (record.get("image") or {}).get("source"),
                (record.get("image") or {}).get("sku"),
            )
            for record in group
        }
        if len(signatures) != 1 or not group:
            continue
        url, source, sku = next(iter(signatures))
        if (
            not isinstance(url, str)
            or image_delivery_rejection_reason(url)
            or source_for_url(url) != source
            or not isinstance(sku, str)
            or not re.fullmatch(r"(?:IND\d+|ARJ\d+)", sku)
            or (source == "Indiana" and not sku.startswith("IND"))
            or (source == "Araujo" and not sku.startswith("ARJ"))
        ):
            continue
        target_group = (
            db.execute(select(CatalogoBase).where(CatalogoBase.name_search == name))
            .scalars()
            .all()
        )
        if len(target_group) != len(group) or not target_group:
            continue
        if any(product.imagem_url not in (None, url) for product in target_group):
            counts["conflicts"].append(
                {
                    "name": name,
                    "reason": "same_name_group_contains_a_different_existing_image",
                }
            )
            continue
        recorded_eans = {
            str((record.get("image") or {}).get("ean") or "").strip()
            for record in group
        }
        recorded_eans.discard("")
        image_ean = next(iter(recorded_eans)) if len(recorded_eans) == 1 else None
        now = datetime.now(UTC)
        added_for_group = 0
        for product in target_group:
            if product.imagem_url == url:
                continue
            product.imagem_url = url
            product.imagem_fonte = source
            product.imagem_sku_origem = sku
            product.imagem_ean = image_ean
            product.imagem_match = "sku_item"
            product.imagem_status = "pendente"
            product.imagem_atualizada_em = now
            product.imagem_verificada_em = None
            product.imagem_ultima_verificacao_em = None
            product.imagem_falhas_consecutivas = 0
            product.imagem_ultima_falha = None
            product.imagem_motivo_rejeicao = None
            if not catalog_image_matches_record(product):
                product.imagem_url = None
                product.imagem_fonte = None
                product.imagem_sku_origem = None
                product.imagem_ean = None
                product.imagem_match = None
                product.imagem_status = None
                product.imagem_atualizada_em = None
                product.imagem_falhas_consecutivas = 0
                counts["invalid"].append(
                    {
                        "name": name,
                        "reason": "group_image_failed_catalog_identity_check",
                    }
                )
                continue
            counts["associated"] += 1
            added_for_group += 1
        unresolved_group_records = sum(
            str((record.get("identity") or {}).get("name") or "").strip() == name
            for _, record in unmatched_records
        )
        if added_for_group == 0:
            counts["already_present"] += unresolved_group_records
        resolved_group_names.add(name)

    counts["unmatched"].extend(
        {"record": label, "ean": (record.get("identity") or {}).get("ean")}
        for label, record in unmatched_records
        if str((record.get("identity") or {}).get("name") or "").strip()
        not in resolved_group_names
    )

    db.commit()
    counts["unmatched_count"] = len(counts["unmatched"])
    counts["conflict_count"] = len(counts["conflicts"])
    counts["invalid_count"] = len(counts["invalid"])
    return counts


def write_export(path: Path, document: dict[str, Any]) -> None:
    """Create a JSON export without overwriting an existing artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        import json

        json.dump(document, output, ensure_ascii=False, indent=2)
        output.write("\n")
