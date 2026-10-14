"""
Módulo contendo o modelo da base de dados local da ANVISA (CMED).
"""

from sqlalchemy import Boolean, Column, Date, Integer, String

from app.models.base import Base


class AnvisaMedicamento(Base):
    """
    Tabela de lookup alimentada pelos dados abertos da ANVISA (CMED)
    para o enriquecimento de medicamentos por EAN.

    Substitui a dependência de APIs externas de consulta de código de barras.
    """

    __tablename__ = "anvisa_medicamentos"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String(14), unique=True, index=True, nullable=False)
    principio_ativo = Column(String)
    laboratorio = Column(String)
    tarja = Column(String)
    registro_anvisa = Column(String(20), nullable=True)
    categoria_regulatoria = Column(String(40), nullable=True)
    status_registro = Column(String(40), nullable=True)
    referencia_anvisa = Column(Boolean, nullable=True)
    exige_receita_confirmada = Column(Boolean, nullable=True)
    controle_especial = Column(Boolean, nullable=True)
    fonte_classificacao = Column(String(120), nullable=True)
    atualizado_fonte_em = Column(Date, nullable=True)
