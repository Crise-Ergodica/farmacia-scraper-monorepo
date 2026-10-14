"""Separate last attempt time from last successful image validation.

Revision ID: e4902ba81c6d
Revises: d31c9a27e4f0
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4902ba81c6d"
down_revision: Union[str, Sequence[str], None] = "d31c9a27e4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "catalogo_base",
        sa.Column(
            "imagem_ultima_verificacao_em", sa.DateTime(timezone=True), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("catalogo_base", "imagem_ultima_verificacao_em")
