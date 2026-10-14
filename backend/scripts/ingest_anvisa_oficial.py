"""Import source-backed regulatory categories from ANVISA open datasets.

Only active, uniquely EAN-to-registration matched products are classified.
Usage: poetry run python scripts/ingest_anvisa_oficial.py CMED.csv REGISTRO.csv
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.anvisa import AnvisaMedicamento
from app.models.catalogo import CatalogoBase

LMR_FILE = (
    Path(__file__).resolve().parents[1] / "data/anvisa_lmr_registros_2026-07-10.txt"
)


def _read(path: str) -> pd.DataFrame:
    return pd.read_csv(
        path, sep=";", dtype=str, keep_default_na=False, encoding="latin1"
    )


def _ean(value: str) -> str | None:
    digits = "".join(c for c in value.strip() if c.isdigit())
    return digits if len(digits) in (13, 14) else None


def build_rows(cmed: pd.DataFrame, registry: pd.DataFrame) -> tuple[list[dict], int]:
    refs = {
        line.strip()
        for line in LMR_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip().isdigit()
    }
    by_registration: dict[str, set[tuple[str, str, str, str]]] = {}
    for _, row in registry.iterrows():
        reg = row.get("NUMERO_REGISTRO_PRODUTO", "").strip()
        status = row.get("SITUACAO_REGISTRO", "").strip().casefold()
        category = row.get("CATEGORIA_REGULATORIA", "").strip()
        if len(reg) != 9 or not category or status != "ativo":
            continue
        by_registration.setdefault(reg, set()).add(
            (
                category,
                reg,
                row.get("PRINCIPIO_ATIVO", "").strip(),
                row.get("EMPRESA_DETENTORA_REGISTRO", "").strip(),
            )
        )

    ean_matches: dict[str, set[tuple[str, str, str, str, str, str]]] = {}
    for _, row in cmed.iterrows():
        reg = row.get("REGISTRO", "").strip()[:9]
        candidates = by_registration.get(reg, set())
        if len(candidates) != 1:
            continue
        category, reg, active, holder = next(iter(candidates))
        for col in ("EAN 1", "EAN 2", "EAN 3"):
            ean = _ean(row.get(col, ""))
            if ean:
                ean_matches.setdefault(ean, set()).add(
                    (
                        category,
                        reg,
                        active,
                        holder,
                        row.get("TARJA", "").strip(),
                        row.get("LABORATÓRIO", "").strip(),
                    )
                )

    output = []
    ambiguous = 0
    for ean, matches in ean_matches.items():
        if len(matches) != 1:
            ambiguous += 1
            continue
        category, reg, active, holder, tariff, lab = next(iter(matches))
        tariff_norm = tariff.casefold()
        recipe = True if "vermelha" in tariff_norm or "preta" in tariff_norm else None
        controlled = True if "preta" in tariff_norm else None
        output.append(
            {
                "ean": ean,
                "principio_ativo": active or None,
                "laboratorio": lab or holder or None,
                "tarja": tariff or None,
                "registro_anvisa": reg,
                "categoria_regulatoria": category,
                "status_registro": "Ativo",
                "referencia_anvisa": reg in refs,
                "exige_receita_confirmada": recipe,
                "controle_especial": controlled,
                "fonte_classificacao": (
                    "ANVISA registro de medicamentos + CMED; LMR 2026-07-10"
                ),
                "atualizado_fonte_em": date(2026, 7, 10),
            }
        )
    return output, ambiguous


def ingest(cmed_path: str, registry_path: str, dry_run: bool = False) -> None:
    rows, ambiguous = build_rows(_read(cmed_path), _read(registry_path))
    print(
        "Classificações únicas e verificadas: "
        f"{len(rows)}; EANs ambíguos ignorados: {ambiguous}"
    )
    if dry_run:
        return
    with SessionLocal() as db:
        for start in range(0, len(rows), 500):
            batch = rows[start : start + 500]
            stmt = insert(AnvisaMedicamento).values(batch)
            updates = {key: stmt.excluded[key] for key in batch[0] if key != "ean"}
            db.execute(stmt.on_conflict_do_update(index_elements=["ean"], set_=updates))
        db.execute(
            CatalogoBase.__table__.update()
            .where(
                CatalogoBase.codigo_barras == AnvisaMedicamento.ean,
                AnvisaMedicamento.categoria_regulatoria.is_not(None),
            )
            .values(
                principio_ativo=func.coalesce(
                    AnvisaMedicamento.principio_ativo,
                    CatalogoBase.principio_ativo,
                ),
                laboratorio=func.coalesce(
                    AnvisaMedicamento.laboratorio,
                    CatalogoBase.laboratorio,
                ),
                categoria_regulatoria=AnvisaMedicamento.categoria_regulatoria,
                referencia_anvisa=AnvisaMedicamento.referencia_anvisa,
                exige_receita_confirmada=AnvisaMedicamento.exige_receita_confirmada,
                controle_especial=AnvisaMedicamento.controle_especial,
                classificacao_fonte=AnvisaMedicamento.fonte_classificacao,
            )
        )
        db.commit()
    print(f"Importação concluída: {len(rows)} linhas verificadas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cmed_csv")
    parser.add_argument("registro_csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ingest(args.cmed_csv, args.registro_csv, args.dry_run)
