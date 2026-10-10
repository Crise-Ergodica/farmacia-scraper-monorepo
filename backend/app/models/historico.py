from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class HistoricoPreco(Base):
    """
    Representa o registro temporal de variações de preço de um medicamento.
    """

    # Nome sem acento para compatibilidade com a infraestrutura existente.
    __tablename__ = "historico_precos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # O nome `medicamento_id` mantém compatibilidade com HistoricoOut.
    medicamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("catalogo_base.id"), nullable=False
    )

    farmacia_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farmacias.id"), nullable=False
    )

    oferta_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ofertas_farmacia.id"), nullable=True, index=True
    )
    origem: Mapped[str | None] = mapped_column(String(40), nullable=True)

    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    disponivel: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data_registro: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
