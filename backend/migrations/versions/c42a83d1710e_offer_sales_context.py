"""Add offer and history sale contexts without changing legacy observations.

Revision ID: c42a83d1710e
Revises: e4902ba81c6d
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c42a83d1710e"
down_revision: Union[str, Sequence[str], None] = "e4902ba81c6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ofertas_farmacia",
        sa.Column(
            "contexto_chave",
            sa.String(120),
            server_default="global",
            nullable=False,
        ),
    )
    for name, length in (
        ("canal_venda", 30),
        ("contexto_local", 40),
        ("cep", 8),
        ("cidade", 100),
        ("uf", 2),
        ("loja_id", 100),
        ("loja_nome", 150),
        ("vendedor", 100),
        ("confiabilidade", 32),
    ):
        op.add_column(
            "ofertas_farmacia", sa.Column(name, sa.String(length), nullable=True)
        )
    op.add_column(
        "ofertas_farmacia",
        sa.Column("fonte_observado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_index("ix_ofertas_farmacia_url_origem", table_name="ofertas_farmacia")
    op.create_index(
        "ix_ofertas_farmacia_url_origem",
        "ofertas_farmacia",
        ["url_origem"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_ofertas_farmacia_url_contexto",
        "ofertas_farmacia",
        ["url_origem", "contexto_chave"],
    )

    op.add_column(
        "historico_precos",
        sa.Column(
            "contexto_chave",
            sa.String(120),
            server_default="global",
            nullable=False,
        ),
    )
    for name, length in (
        ("canal_venda", 30),
        ("contexto_local", 40),
        ("cep", 8),
        ("cidade", 100),
        ("uf", 2),
        ("loja_id", 100),
        ("loja_nome", 150),
    ):
        op.add_column(
            "historico_precos", sa.Column(name, sa.String(length), nullable=True)
        )
    op.add_column(
        "historico_precos",
        sa.Column("fonte_observado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "identidades_catalogo_fonte",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmacia_id", sa.Integer(), nullable=False),
        sa.Column("sku_fonte", sa.String(80), nullable=False),
        sa.Column("catalogo_id", sa.Integer(), nullable=False),
        sa.Column("url_canonica", sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(["farmacia_id"], ["farmacias.id"]),
        sa.ForeignKeyConstraint(["catalogo_id"], ["catalogo_base.id"]),
        sa.UniqueConstraint(
            "farmacia_id", "sku_fonte", name="uq_identidade_fonte_farmacia_sku"
        ),
    )


def downgrade() -> None:
    duplicate_context_urls = op.get_bind().execute(
        sa.text(
            "SELECT url_origem FROM ofertas_farmacia "
            "GROUP BY url_origem HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate_context_urls:
        raise RuntimeError(
            "Downgrade inseguro: ofertas com contextos distintos compartilham URL."
        )
    op.drop_table("identidades_catalogo_fonte")
    op.drop_column("historico_precos", "fonte_observado_em")
    op.drop_column("historico_precos", "loja_id")
    op.drop_column("historico_precos", "loja_nome")
    op.drop_column("historico_precos", "uf")
    op.drop_column("historico_precos", "cidade")
    op.drop_column("historico_precos", "cep")
    op.drop_column("historico_precos", "contexto_local")
    op.drop_column("historico_precos", "canal_venda")
    op.drop_column("historico_precos", "contexto_chave")
    op.drop_constraint(
        "uq_ofertas_farmacia_url_contexto", "ofertas_farmacia", type_="unique"
    )
    op.drop_index("ix_ofertas_farmacia_url_origem", table_name="ofertas_farmacia")
    op.create_index(
        "ix_ofertas_farmacia_url_origem",
        "ofertas_farmacia",
        ["url_origem"],
        unique=True,
    )
    op.drop_column("ofertas_farmacia", "confiabilidade")
    op.drop_column("ofertas_farmacia", "fonte_observado_em")
    op.drop_column("ofertas_farmacia", "vendedor")
    op.drop_column("ofertas_farmacia", "loja_id")
    op.drop_column("ofertas_farmacia", "loja_nome")
    op.drop_column("ofertas_farmacia", "uf")
    op.drop_column("ofertas_farmacia", "cidade")
    op.drop_column("ofertas_farmacia", "cep")
    op.drop_column("ofertas_farmacia", "contexto_local")
    op.drop_column("ofertas_farmacia", "canal_venda")
    op.drop_column("ofertas_farmacia", "contexto_chave")
