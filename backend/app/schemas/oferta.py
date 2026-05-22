"""
Módulo responsável pela definição dos contratos de dados (Schemas) de Ofertas Locais.
"""
from decimal import Decimal
from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, constr, field_validator

class ProdutoExtraidoSchema(BaseModel):
    """
    Schema estrito para validação dos dados brutos extraídos pelos scrapers
    antes de serem processados para inserção no banco de dados.
    """
    id: str | int = Field(..., description="ID interno do produto no scraper")
    sku_interno: str = Field(..., description="SKU local único da farmácia para a oferta")
    ean: str | None = Field(default=None, max_length=14, pattern=r"^\d+$", description="Código de barras EAN estritamente numérico")
    name_search: str = Field(..., max_length=150, description="Nome do produto padronizado para busca")

    @field_validator('ean', mode='before')
    @classmethod
    def limpar_ean(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().replace("-", "").replace(" ", "")
            if not v:
                return None
        return v

    preco: float = Field(default=0.0, ge=0.0, description="Preço do produto (precisão flutuante inicial)")
    link: str = Field(..., max_length=500, description="URL de origem do produto")
    imagem_url: str | None = Field(default=None, max_length=500, description="URL da imagem do produto")

class OfertaBaseSchema(BaseModel):
    """
    Schema base contendo os atributos voláteis de precificação e estoque.
    """
    preco: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    quantidade_estoque: int = Field(default=0, ge=0)
    disponivel: bool = Field(default=True)
    url_origem: str 
    imagem_url: str | None = None

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