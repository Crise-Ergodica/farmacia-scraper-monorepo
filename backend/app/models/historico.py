from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class HistoricoPreco(Base):
    """
    Representa o registro temporal de variações de preço de um medicamento.

    Esta classe funciona como uma tabela de log/histórico, vinculando um 
    medicamento específico a uma farmácia e registrando o valor praticado
    em um determinado momento no tempo.

    :param id: Identificador único e chave primária do registro de histórico.
    :type id: int
    :param medicamento_id: Chave estrangeira que vincula o preço ao medicamento.
    :type medicamento_id: int
    :param farmacia_id: Chave estrangeira que vincula o preço à farmácia de origem.
    :type farmacia_id: int
    :param preco: Valor monetário do medicamento (até 10 dígitos, 2 decimais).
    :type preco: decimal.Decimal
    :param data_registro: Timestamp de quando o preço foi capturado ou atualizado.
    :type data_registro: datetime.datetime
    """
    __tablename__ = "historico_preços"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medicamento_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicamentos.id"), nullable=False)
    farmacia_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmacias.id"), nullable=False)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_registro: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)