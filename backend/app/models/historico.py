from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class HistoricoPreco(Base):
    """
    Representa o registro temporal de variações de preço de um medicamento.
    """
    # precos (sem cedilha) ao invés de preços para garantir compatibilidade universal de infraestrutura.
    __tablename__ = "historico_precos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # CORREÇÃO DA FALHA: O ForeignKey agora aponta para a tabela física correta existente no metadado.
    # Mantive o nome da coluna como `medicamento_id` para não quebrar seu schema HistoricoOut do FastAPI.
    medicamento_id: Mapped[int] = mapped_column(Integer, ForeignKey("catalogo_base.id"), nullable=False)
    
    farmacia_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmacias.id"), nullable=False)
    
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_registro: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)