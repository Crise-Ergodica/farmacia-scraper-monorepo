"""Add validated catalog image references and price observation metadata.

Revision ID: 3a72d8ce1f40
Revises: 2fb279b2e8b3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3a72d8ce1f40"
down_revision: Union[str, Sequence[str], None] = "2fb279b2e8b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "catalogo_base", sa.Column("imagem_url", sa.String(500), nullable=True)
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_fonte", sa.String(40), nullable=True)
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_sku_origem", sa.String(80), nullable=True)
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_ean", sa.String(14), nullable=True)
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_match", sa.String(24), nullable=True)
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_status", sa.String(20), nullable=True)
    )
    op.add_column(
        "catalogo_base",
        sa.Column("imagem_verificada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "catalogo_base", sa.Column("imagem_motivo_rejeicao", sa.Text(), nullable=True)
    )
    op.add_column(
        "ofertas_farmacia",
        sa.Column("observado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "historico_precos",
        sa.Column("oferta_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_historico_precos_oferta_id_ofertas_farmacia",
        "historico_precos",
        "ofertas_farmacia",
        ["oferta_id"],
        ["id"],
    )
    op.create_index("ix_historico_precos_oferta_id", "historico_precos", ["oferta_id"])
    op.add_column("historico_precos", sa.Column("origem", sa.String(40), nullable=True))
    op.add_column(
        "historico_precos", sa.Column("disponivel", sa.Boolean(), nullable=True)
    )
    op.create_index(
        "ix_historico_precos_medicamento_farmacia_data",
        "historico_precos",
        ["medicamento_id", "farmacia_id", "data_registro"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_historico_precos_medicamento_farmacia_data",
        table_name="historico_precos",
    )
    op.drop_column("historico_precos", "disponivel")
    op.drop_column("historico_precos", "origem")
    op.drop_index("ix_historico_precos_oferta_id", table_name="historico_precos")
    op.drop_constraint(
        "fk_historico_precos_oferta_id_ofertas_farmacia",
        "historico_precos",
        type_="foreignkey",
    )
    op.drop_column("historico_precos", "oferta_id")
    op.drop_column("ofertas_farmacia", "observado_em")
    for column in (
        "imagem_motivo_rejeicao",
        "imagem_verificada_em",
        "imagem_status",
        "imagem_match",
        "imagem_ean",
        "imagem_sku_origem",
        "imagem_fonte",
        "imagem_url",
    ):
        op.drop_column("catalogo_base", column)
