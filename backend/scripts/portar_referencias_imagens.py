"""Export/import stable image references (no prices, accounts, or local-ID matching)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.image_reference_portability import (
    export_image_references,
    import_image_references,
    write_export,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export_parser = commands.add_parser("export", help="Exportar as referências atuais")
    export_parser.add_argument("--output", type=Path, required=True)
    import_parser = commands.add_parser(
        "import", help="Importar para o PostgreSQL configurado"
    )
    import_parser.add_argument("--input", type=Path, required=True)
    import_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.command == "export":
            document = export_image_references(db)
            write_export(args.output, document)
            print(
                json.dumps(
                    {"exported": document["record_count"], "path": str(args.output)}
                )
            )
            return 0

        if args.report.exists():
            parser.error(f"O relatório já existe e não será sobrescrito: {args.report}")
        document = json.loads(args.input.read_text(encoding="utf-8"))
        result = import_image_references(db, document)
    report = {
        "schema": "preco-bao.image-reference-import-log",
        "schema_version": 1,
        "imported_at": datetime.now(UTC).isoformat(),
        "source_exported_at": document.get("exported_at"),
        **result,
    }
    write_export(args.report, report)
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)}
        )
    )
    return (
        0
        if not (result["conflicts"] or result["unmatched"] or result["invalid"])
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
