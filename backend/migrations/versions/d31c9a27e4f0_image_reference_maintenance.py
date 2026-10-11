"""Track image reference updates and consecutive validation failures.

Revision ID: d31c9a27e4f0
Revises: 7a81c20f5d31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d31c9a27e4f0"
down_revision: Union[str, Sequence[str], None] = "7a81c20f5d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "catalogo_base",
        sa.Column("imagem_atualizada_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "catalogo_base",
        sa.Column(
            "imagem_falhas_consecutivas",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "catalogo_base",
        sa.Column("imagem_ultima_falha", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("catalogo_base", "imagem_ultima_falha")
    op.drop_column("catalogo_base", "imagem_falhas_consecutivas")
    op.drop_column("catalogo_base", "imagem_atualizada_em")
