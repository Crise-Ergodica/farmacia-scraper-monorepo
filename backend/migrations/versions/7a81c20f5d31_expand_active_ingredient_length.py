"""Allow full official names for combination active ingredients.

Revision ID: 7a81c20f5d31
Revises: 4c719abd20ae
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7a81c20f5d31"
down_revision: Union[str, Sequence[str], None] = "4c719abd20ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "catalogo_base",
        "principio_ativo",
        existing_type=sa.String(length=150),
        type_=sa.String(length=500),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "catalogo_base",
        "principio_ativo",
        existing_type=sa.String(length=500),
        type_=sa.String(length=150),
        existing_nullable=False,
    )
