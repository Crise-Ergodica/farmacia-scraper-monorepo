"""Add Usuario model and favorites

Revision ID: 2fb279b2e8b3
Revises: e0c4fa285a00
Create Date: 2026-06-10 12:45:53.025501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '2fb279b2e8b3'
down_revision: Union[str, Sequence[str], None] = 'e0c4fa285a00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('usuario',
    sa.Column('id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuario'))
    )
    op.create_index(op.f('ix_usuario_email'), 'usuario', ['email'], unique=True)

    op.create_table('usuario_farmacia_favorita',
    sa.Column('usuario_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('farmacia_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['farmacia_id'], ['farmacias.id'], name=op.f('fk_usuario_farmacia_favorita_farmacia_id_farmacias'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_usuario_farmacia_favorita_usuario_id_usuario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'farmacia_id', name=op.f('pk_usuario_farmacia_favorita'))
    )

    op.create_table('usuario_medicamento_favorito',
    sa.Column('usuario_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('medicamento_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['medicamento_id'], ['catalogo_base.id'], name=op.f('fk_usuario_medicamento_favorito_medicamento_id_catalogo_base'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_usuario_medicamento_favorito_usuario_id_usuario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'medicamento_id', name=op.f('pk_usuario_medicamento_favorito'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('usuario_medicamento_favorito')
    op.drop_table('usuario_farmacia_favorita')
    op.drop_index(op.f('ix_usuario_email'), table_name='usuario')
    op.drop_table('usuario')
