from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class HistoricoPreco(Base):
    """
    Representa o registro temporal de variações de preço de um medicamento.
    """

    # Nome sem acento para compatibilidade com a infraestrutura existente.
    __tablename__ = "historico_precos"
    __table_args__ = (
        Index(
            "ix_historico_precos_medicamento_farmacia_data",
            "medicamento_id",
            "farmacia_id",
            "data_registro",
        ),
    )

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
    contexto_chave: Mapped[str] = mapped_column(
        String(120), nullable=False, default="global", server_default="global"
    )
    canal_venda: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contexto_local: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    loja_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    loja_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    fonte_observado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    disponivel: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data_registro: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
