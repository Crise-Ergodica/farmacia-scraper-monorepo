"""Read-only catalog-wide audit of current offers and genuine price events."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.core.database import SessionLocal
from app.scrapers.offer_refresh import STATE_DIR


def audit() -> dict:
    with SessionLocal() as db:
        rows = (
            db.execute(
                text("""
            SELECT f.id, f.nome_fantasia, COUNT(o.id) AS offers,
                   COUNT(o.observado_em) AS observed_offers,
                   COUNT(*) FILTER (WHERE o.disponivel) AS available_offers
            FROM farmacias f LEFT JOIN ofertas_farmacia o ON o.farmacia_id=f.id
            GROUP BY f.id, f.nome_fantasia ORDER BY f.id
        """)
            )
            .mappings()
            .all()
        )
        pharmacies = []
        for row in rows:
            source_state = None
            source = {"Indiana": "indiana", "Araujo": "araujo"}.get(
                row["nome_fantasia"]
            )
            if source:
                try:
                    checkpoint = json.loads(
                        (STATE_DIR / f"{source}.json").read_text(encoding="utf-8")
                    )
                    source_state = {
                        key: checkpoint.get(key)
                        for key in ("cursor", "updated_at", "stop_reason", "errors")
                    }
                except (OSError, ValueError):
                    source_state = {"status": "source_not_consulted"}
            events = (
                db.execute(
                    text("""
                SELECT COUNT(*) AS events,
                       COUNT(DISTINCT medicamento_id) AS medicines_with_events,
                       COUNT(*) FILTER (WHERE oferta_id IS NULL) AS legacy_unlinked
                FROM historico_precos WHERE farmacia_id=:id
            """),
                    {"id": row["id"]},
                )
                .mappings()
                .one()
            )
            current_with_history = db.scalar(
                text("""
                SELECT COUNT(DISTINCT o.catalogo_id) FROM ofertas_farmacia o
                WHERE o.farmacia_id=:id AND EXISTS (
                    SELECT 1 FROM historico_precos h
                    WHERE h.medicamento_id=o.catalogo_id AND h.farmacia_id=o.farmacia_id
                )
            """),
                {"id": row["id"]},
            )
            pharmacies.append(
                {
                    **dict(row),
                    **dict(events),
                    "current_medicines_with_history": current_with_history,
                    "source_refresh": source_state,
                }
            )
        counts = (
            db.execute(
                text("""
            WITH current AS (
                SELECT DISTINCT catalogo_id, farmacia_id FROM ofertas_farmacia
                WHERE disponivel AND preco > 0
            ), multi AS (
                SELECT catalogo_id FROM current GROUP BY catalogo_id
                HAVING COUNT(*) > 1
            )
            SELECT COUNT(*) AS multi_medicines,
                   COUNT(*) FILTER (WHERE NOT EXISTS (
                       SELECT 1 FROM current c WHERE c.catalogo_id=m.catalogo_id
                       AND NOT EXISTS (
                           SELECT 1 FROM historico_precos h
                           WHERE h.medicamento_id=c.catalogo_id
                           AND h.farmacia_id=c.farmacia_id
                       )
                   )) AS complete_history,
                   COUNT(*) FILTER (WHERE EXISTS (
                       SELECT 1 FROM current c WHERE c.catalogo_id=m.catalogo_id
                       AND NOT EXISTS (
                           SELECT 1 FROM historico_precos h
                           WHERE h.medicamento_id=c.catalogo_id
                           AND h.farmacia_id=c.farmacia_id
                       )
                   )) AS incomplete_history
            FROM multi m
        """)
            )
            .mappings()
            .one()
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "pharmacies": pharmacies,
        "multiple_pharmacies": dict(counts),
    }


def missing_current_offers() -> list[dict]:
    """List current source offers for which no real pharmacy event exists."""
    with SessionLocal() as db:
        rows = (
            db.execute(
                text("""
            SELECT o.catalogo_id AS medicamento_id, c.name_search AS medicamento,
                   o.farmacia_id, f.nome_fantasia AS farmacia, o.id AS oferta_id,
                   o.sku_interno, o.preco, o.observado_em
            FROM ofertas_farmacia o
            JOIN catalogo_base c ON c.id=o.catalogo_id
            JOIN farmacias f ON f.id=o.farmacia_id
            WHERE o.disponivel AND o.preco>0 AND NOT EXISTS (
                SELECT 1 FROM historico_precos h
                WHERE h.medicamento_id=o.catalogo_id AND h.farmacia_id=o.farmacia_id
            )
            ORDER BY o.farmacia_id, o.id
        """)
            )
            .mappings()
            .all()
        )
    return [
        {**dict(row), "observado_em": str(row["observado_em"] or "")} for row in rows
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--missing-output", type=Path)
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.missing_output:
        args.missing_output.parent.mkdir(parents=True, exist_ok=True)
        missing = missing_current_offers()
        with args.missing_output.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "medicamento_id",
                    "medicamento",
                    "farmacia_id",
                    "farmacia",
                    "oferta_id",
                    "sku_interno",
                    "preco",
                    "observado_em",
                ],
            )
            writer.writeheader()
            writer.writerows(missing)
    print(rendered)
