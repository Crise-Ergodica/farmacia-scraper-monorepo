"""
Módulo responsável pela definição do modelo de Oferta e Estoque Local.
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class OfertaFarmacia(Base):
    """
    Representa a precificação e a disponibilidade física de um item do catálogo em uma loja.

    :ivar id: Identificador único e chave primária da oferta.
    :vartype id: int
    :ivar preco: Valor de venda local do medicamento (precisão monetária).
    :vartype preco: Decimal
    :ivar quantidade_estoque: Quantidade de unidades disponíveis fisicamente.
    :vartype quantidade_estoque: int
    :ivar disponivel: Flag indicando se a oferta está ativa para o público.
    :vartype disponivel: bool
    :ivar url_origem: Link direto para a compra ou visualização no site da farmácia.
    :vartype url_origem: str
    :ivar imagem_url: Link da fotografia ilustrativa retirada do scrape.
    :vartype imagem_url: str | None
    :ivar criado_em: Timestamp de criação do registro da oferta.
    :vartype criado_em: datetime
    :ivar atualizado_em: Timestamp de alteração (ex: mudança de preço/estoque).
    :vartype atualizado_em: datetime | None
    :ivar farmacia_id: Chave estrangeira que vincula a oferta à farmácia.
    :vartype farmacia_id: int
    :ivar catalogo_id: Chave estrangeira que vincula a oferta ao catálogo global.
    :vartype catalogo_id: int
    :ivar farmacia: Relacionamento ORM com a entidade Farmacia.
    :vartype farmacia: Farmacia
    :ivar produto_catalogo: Relacionamento ORM com a entidade CatalogoBase.
    :vartype produto_catalogo: CatalogoBase
    """
    __tablename__ = "ofertas_farmacia"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku_interno: Mapped[str] = mapped_column(String(50), index=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
    url_origem: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    imagem_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    farmacia_id: Mapped[int] = mapped_column(ForeignKey("farmacias.id"))
    catalogo_id: Mapped[int] = mapped_column(ForeignKey("catalogo_base.id"))

    farmacia: Mapped["Farmacia"] = relationship("Farmacia", back_populates="ofertas")
    produto_catalogo: Mapped["CatalogoBase"] = relationship("CatalogoBase", back_populates="ofertas")