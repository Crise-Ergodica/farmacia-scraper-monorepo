"""Reclassify exact catalog URLs whose inspected bytes are generic templates."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CatalogoBase
from app.services.imagens import KNOWN_GENERIC_CONTENT_HASHES

REPORTS = Path(__file__).resolve().parents[1] / "reports"
HASHES = {
    "Araujo": REPORTS / "araujo-image-hashes.json",
    "Indiana": REPORTS / "indiana-image-hashes.json",
}
OUTPUT = REPORTS / "generic-content-reclassification.json"
GENERIC_URLS = REPORTS.parent / "app" / "services" / "generic_image_urls.json"
ALTERNATIVE_HASHES = REPORTS / "alternative-image-hashes.json"


def main() -> None:
    checks = {
        source: json.loads(path.read_text(encoding="utf-8"))
        for source, path in HASHES.items()
    }
    if ALTERNATIVE_HASHES.exists():
        checks["Araujo"].update(
            json.loads(ALTERNATIVE_HASHES.read_text(encoding="utf-8"))
        )
    generic_urls = sorted(
        url
        for source_checks in checks.values()
        for url, check in source_checks.items()
        if check.get("status") == 200
        and check.get("sha256") in KNOWN_GENERIC_CONTENT_HASHES
    )
    GENERIC_URLS.write_text(
        json.dumps(
            {
                "description": (
                    "Exact URLs with visually confirmed generic response bytes."
                ),
                "urls": generic_urls,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    ids = []
    by_hash = Counter()
    with SessionLocal() as db:
        rows = db.execute(
            select(CatalogoBase)
            .where(CatalogoBase.imagem_status == "verificada")
            .order_by(CatalogoBase.id)
        ).scalars()
        for item in rows:
            check = checks.get(item.imagem_fonte or "", {}).get(
                item.imagem_url or "", {}
            )
            digest = check.get("sha256")
            if check.get("status") != 200 or digest not in KNOWN_GENERIC_CONTENT_HASHES:
                continue
            item.imagem_status = "pendente"
            item.imagem_verificada_em = None
            item.imagem_motivo_rejeicao = (
                f"O conteúdo é uma ilustração genérica da farmácia. SHA-256: {digest}."
            )
            ids.append(item.id)
            by_hash[digest] += 1
            if len(ids) % 50 == 0:
                db.commit()
                print(f"Reclassified {len(ids)} exact URL matches.", flush=True)
        db.commit()
    previous_ids = set(previous.get("reclassified_ids", []))
    previous_counts = Counter(previous.get("reclassified_by_hash", {}))
    OUTPUT.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reclassified_ids": sorted(previous_ids.union(ids)),
                "reclassified_by_hash": previous_counts + by_hash,
                "source_hash_files": [
                    path.name for path in (*HASHES.values(), ALTERNATIVE_HASHES)
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Reclassified {len(ids)} catalog images.")


if __name__ == "__main__":
    main()
