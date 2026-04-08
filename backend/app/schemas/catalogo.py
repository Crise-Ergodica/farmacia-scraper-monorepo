"""
Módulo responsável pela definição dos contratos de dados (Schemas) do Catálogo.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .oferta import OfertaOut

class CatalogoBaseSchema(BaseModel):
    """
    Schema base contendo os atributos invariáveis do produto farmacêutico.
    """
    codigo_barras: str = Field(..., max_length=13, description="Código EAN de 13 dígitos")
    nome: str = Field(..., max_length=150)
    principio_ativo: str = Field(..., max_length=150)
    laboratorio: str = Field(..., max_length=100)
    exige_receita: bool = Field(default=False)

class CatalogoOut(CatalogoBaseSchema):
    """
    Schema de saída (Response) para a entidade de Catálogo.
    Inclui os metadados gerados pelo banco de dados e permite leitura via ORM.
    """
    id: int
    criado_em: datetime
    atualizado_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CatalogoComOfertasOut(CatalogoOut):
    """
    Schema agregado que compila um item do catálogo com todas as suas ofertas ativas.
    Ideal para o endpoint principal de pesquisa do aplicativo móvel.
    """
    ofertas: list[OfertaOut] = Field(default_factory=list)