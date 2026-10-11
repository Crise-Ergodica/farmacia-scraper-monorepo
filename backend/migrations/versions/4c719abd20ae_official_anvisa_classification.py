"""Add nullable, source-backed ANVISA classification fields.

Revision ID: 4c719abd20ae
Revises: 3a72d8ce1f40
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4c719abd20ae"
down_revision: Union[str, Sequence[str], None] = "3a72d8ce1f40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("catalogo_base", "anvisa_medicamentos"):
        op.add_column(
            table, sa.Column("categoria_regulatoria", sa.String(40), nullable=True)
        )
    for name in ("referencia_anvisa", "exige_receita_confirmada", "controle_especial"):
        op.add_column("catalogo_base", sa.Column(name, sa.Boolean(), nullable=True))
        op.add_column(
            "anvisa_medicamentos", sa.Column(name, sa.Boolean(), nullable=True)
        )
    op.add_column(
        "catalogo_base", sa.Column("classificacao_fonte", sa.String(80), nullable=True)
    )
    op.add_column(
        "anvisa_medicamentos",
        sa.Column("registro_anvisa", sa.String(20), nullable=True),
    )
    op.add_column(
        "anvisa_medicamentos",
        sa.Column("status_registro", sa.String(40), nullable=True),
    )
    op.add_column(
        "anvisa_medicamentos",
        sa.Column("fonte_classificacao", sa.String(120), nullable=True),
    )
    op.add_column(
        "anvisa_medicamentos",
        sa.Column("atualizado_fonte_em", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    for table, columns in {
        "catalogo_base": (
            "classificacao_fonte",
            "controle_especial",
            "exige_receita_confirmada",
            "referencia_anvisa",
            "categoria_regulatoria",
        ),
        "anvisa_medicamentos": (
            "atualizado_fonte_em",
            "fonte_classificacao",
            "status_registro",
            "registro_anvisa",
            "controle_especial",
            "exige_receita_confirmada",
            "referencia_anvisa",
            "categoria_regulatoria",
        ),
    }.items():
        for column in columns:
            op.drop_column(table, column)
