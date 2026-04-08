"""
Módulo responsável pela definição do modelo central de Catálogo de Medicamentos.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
from .oferta_farmacia import OfertaFarmacia

class CatalogoBase(Base):
    """
    Representa o catálogo unificado com dados farmacológicos invariáveis.

    :ivar id: Identificador único e chave primária do produto no catálogo.
    :vartype id: int
    :ivar codigo_barras: Código EAN de 13 dígitos, com restrição de unicidade.
    :vartype codigo_barras: str
    :ivar nome: Nome comercial padronizado do medicamento.
    :vartype nome: str
    :ivar principio_ativo: Substrato químico ou princípio ativo principal.
    :vartype principio_ativo: str
    :ivar laboratorio: Nome do fabricante ou detentor do registro.
    :vartype laboratorio: str
    :ivar exige_receita: Indica se o medicamento é de uso controlado.
    :vartype exige_receita: bool
    :ivar criado_em: Timestamp gerado automaticamente na inserção.
    :vartype criado_em: datetime
    :ivar atualizado_em: Timestamp atualizado automaticamente em modificações.
    :vartype atualizado_em: datetime | None
    :ivar ofertas: Relacionamento reverso com as ofertas ativas nas farmácias.
    :vartype ofertas: list['OfertaFarmacia']
    """
    __tablename__ = "catalogo_base"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo_barras: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), index=True)
    principio_ativo: Mapped[str] = mapped_column(String(150), index=True)
    laboratorio: Mapped[str] = mapped_column(String(100), index=True)
    exige_receita: Mapped[bool] = mapped_column(Boolean, default=False)
    
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    ofertas: Mapped[list["OfertaFarmacia"]] = relationship("OfertaFarmacia", back_populates="produto_catalogo")