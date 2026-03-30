"""
Módulo responsável pela definição do modelo de dados de Medicamentos.
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

class Medicamento(Base):
    """
    Representa a entidade Medicamento no banco de dados.

    Esta classe mapeia a tabela 'medicamentos', mantendo o registro de
    produtos farmacêuticos, precificação exata e rastreabilidade temporal.

    :param id: Identificador único e chave primária do medicamento.
    :type id: int
    :param codigo_barras: Código EAN de 13 dígitos, com restrição de unicidade.
    :type codigo_barras: str
    :param nome: Nome comercial do medicamento.
    :type nome: str
    :param principio_ativo: Substrato químico ou princípio ativo principal.
    :type principio_ativo: str
    :param laboratorio: Nome do fabricante do medicamento.
    :type laboratorio: str
    :param preco: Valor de venda do medicamento (precisão monetária).
    :type preco: decimal.Decimal
    :param exige_receita: Flag que indica se o medicamento é de uso controlado.
    :type exige_receita: bool
    :param quantidade_estoque: Quantidade de unidades disponíveis fisicamente.
    :type quantidade_estoque: int
    :param disponivel: Flag de exclusão lógica ou disponibilidade de venda do produto.
    :type disponivel: bool
    :param url_origem: Link de referência externa ou fonte da extração de dados do medicamento.
    :type url_origem: str
    :param imagem_url: Link da fotografia ou imagem ilustrativa do medicamento no site de origem.
    :type imagem_url: str
    :param criado_em: Timestamp gerado automaticamente na inserção do registro.
    :type criado_em: datetime.datetime
    :param atualizado_em: Timestamp atualizado automaticamente em modificações.
    :type atualizado_em: datetime.datetime
    :param farmacia_id: Chave estrangeira que vincula o medicamento à farmácia.
    :type farmacia_id: int
    :param farmacia: Relacionamento ORM reverso com a entidade Farmacia.
    :type farmacia: Farmacia
    """
    __tablename__ = "medicamentos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo_barras: Mapped[str] = mapped_column(String(13), unique=True, index=True) 
    nome: Mapped[str] = mapped_column(String(150), index=True)
    principio_ativo: Mapped[str] = mapped_column(String(150), index=True)
    laboratorio: Mapped[str] = mapped_column(String(100), index=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    exige_receita: Mapped[bool] = mapped_column(Boolean, default=False)
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
    url_origem: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    imagem_url: Mapped[str] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    farmacia_id: Mapped[int] = mapped_column(ForeignKey("farmacias.id"))
    farmacia = relationship("Farmacia", back_populates="medicamentos")