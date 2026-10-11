"""Report persistent image reference and identity coverage without network calls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CatalogoBase
from app.services.imagens import (
    catalog_image_matches_record,
    image_delivery_rejection_reason,
    image_rejection_reason,
)


def main() -> int:
    with SessionLocal() as db:
        products = db.execute(select(CatalogoBase)).scalars().all()
    referenced = [item for item in products if item.imagem_url]
    technically_eligible = [
        item
        for item in referenced
        if not image_delivery_rejection_reason(item.imagem_url)
    ]
    identity_eligible = [
        item for item in technically_eligible if catalog_image_matches_record(item)
    ]
    generic_classified = [
        item for item in identity_eligible if image_rejection_reason(item.imagem_url)
    ]
    report = {
        "catalog_products": len(products),
        "with_image_reference": len(referenced),
        "technically_eligible_references": len(technically_eligible),
        "identity_eligible_references": len(identity_eligible),
        "missing_references": len(products) - len(referenced),
        "identity_or_safety_rejected": len(products) - len(identity_eligible),
        "unique_reference_urls": len({item.imagem_url for item in referenced}),
        "generic_markers_or_hashes": len(generic_classified),
        "unclassified_or_specific_candidates": len(identity_eligible)
        - len(generic_classified),
        "generic_marker_note": (
            "Classification uses known URL/hash markers; it is not visual proof."
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["identity_or_safety_rejected"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
