"""
Módulo responsável pela definição dos contratos de dados (Schemas) de Ofertas Locais.
"""
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class OfertaBaseSchema(BaseModel):
    """
    Schema base contendo os atributos voláteis de precificação e estoque.
    """
    preco: Decimal = Field(..., max_digits=10, decimal_places=2)
    quantidade_estoque: int = Field(default=0, ge=0)
    disponivel: bool = Field(default=True)
    url_origem: HttpUrl
    imagem_url: HttpUrl | None = None

class OfertaOut(OfertaBaseSchema):
    """
    Schema de saída (Response) para a entidade de Oferta.
    Mapeia as chaves estrangeiras cruciais para a interface gráfica.
    """
    id: int
    farmacia_id: int
    catalogo_id: int
    criado_em: datetime
    atualizado_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)