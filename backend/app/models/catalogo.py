"""
Módulo responsável pela definição do modelo central de Catálogo de Medicamentos.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY  # Importação específica para o Postgres

from .base import Base
from .oferta_farmacia import OfertaFarmacia
from .historico import HistoricoPreco

class CatalogoBase(Base):
    """
    Representa o catálogo unificado com dados farmacológicos invariáveis.
    """
    __tablename__ = "catalogo_base"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(14), unique=True, index=True, nullable=True)
    name_search: Mapped[str] = mapped_column(String(150), index=True)
    
    principio_ativo: Mapped[str] = mapped_column(String(150), index=True, default="Não informado")
    laboratorio: Mapped[str] = mapped_column(String(100), index=True, default="Não informado")
    exige_receita: Mapped[bool] = mapped_column(Boolean, default=False)
    
    categorias: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


    ofertas: Mapped[list["OfertaFarmacia"]] = relationship("OfertaFarmacia", back_populates="produto_catalogo")
    historico_precos: Mapped[list["HistoricoPreco"]] = relationship("HistoricoPreco", backref="medicamento", cascade="all, delete-orphan")