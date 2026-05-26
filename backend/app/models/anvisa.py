"""
Módulo contendo o modelo da base de dados local da ANVISA (CMED).
"""
from sqlalchemy import Column, Integer, String
from app.models.base import Base

class AnvisaMedicamento(Base):
    """
    Tabela de lookup local (Lookup Table) alimentada pelos dados abertos da ANVISA (CMED)
    para o enriquecimento de medicamentos por EAN.

    Substitui a dependência de APIs externas de consulta de código de barras.
    """
    __tablename__ = "anvisa_medicamentos"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String(14), unique=True, index=True, nullable=False)
    principio_ativo = Column(String)
    laboratorio = Column(String)
    tarja = Column(String)
