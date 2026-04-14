"""
Módulo responsável pela definição do modelo de dados de Farmácias.
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
from .oferta_farmacia import OfertaFarmacia

class Farmacia(Base):
    """
    Representa a entidade corporativa e física da Farmácia no banco de dados.

    Esta classe gerencia os dados cadastrais, a localização geográfica precisa 
    e o relacionamento com o inventário de medicamentos disponíveis.

    :param id: Identificador único e chave primária da farmácia.
    :type id: int
    :param cnpj: Cadastro Nacional da Pessoa Jurídica (apenas números), único.
    :type cnpj: str
    :param razao_social: Nome legal da empresa registrado na Receita Federal.
    :type razao_social: str
    :param nome_fantasia: Nome comercial ou marca da farmácia.
    :type nome_fantasia: str
    :param telefone: Número de telefone principal para contato.
    :type telefone: str
    :param endereco_completo: Endereço físico concatenado ou descritivo.
    :type endereco_completo: str
    :param latitude: Coordenada geográfica de latitude com 6 casas decimais.
    :type latitude: decimal.Decimal
    :param longitude: Coordenada geográfica de longitude com 6 casas decimais.
    :type longitude: decimal.Decimal
    :param criado_em: Timestamp de criação do registro da farmácia.
    :type criado_em: datetime.datetime
    :param atualizado_em: Timestamp da última alteração no cadastro.
    :type atualizado_em: datetime.datetime
    :param medicamentos: Coleção de medicamentos associados a esta farmácia.
    :type medicamentos: list[Medicamento]
    """
    __tablename__ = "farmacias"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(150))
    nome_fantasia: Mapped[str] = mapped_column(String(100), index=True)
    telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    endereco_completo: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    ofertas: Mapped[list["OfertaFarmacia"]] = relationship("OfertaFarmacia", back_populates="farmacia", cascade="all, delete-orphan")