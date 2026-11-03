"""Legacy generic source-SKU mapping retained for Alembic compatibility.

Revision ``c42a83d1710e`` was applied to the isolated PostgreSQL homologation
database. Keep this mapping in ORM metadata so existing schemas remain
recognizable; no active importer currently writes to it.
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IdentidadeCatalogoFonte(Base):
    __tablename__ = "identidades_catalogo_fonte"
    __table_args__ = (
        UniqueConstraint(
            "farmacia_id", "sku_fonte", name="uq_identidade_fonte_farmacia_sku"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    farmacia_id: Mapped[int] = mapped_column(ForeignKey("farmacias.id"), nullable=False)
    sku_fonte: Mapped[str] = mapped_column(String(80), nullable=False)
    catalogo_id: Mapped[int] = mapped_column(
        ForeignKey("catalogo_base.id"), nullable=False
    )
    url_canonica: Mapped[str] = mapped_column(String(500), nullable=False)
