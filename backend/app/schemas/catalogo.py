"""
Módulo responsável pela definição dos contratos de dados (Schemas) do Catálogo.
"""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from .oferta import OfertaOut

class CatalogoBaseSchema(BaseModel):
    """
    Schema base contendo os atributos invariáveis do produto farmacêutico.
    """
    codigo_barras: str | None = Field(default=None, max_length=14, description="Código EAN de até 14 dígitos")
    name_search: str = Field(..., max_length=150)
    principio_ativo: str = Field(default="Não informado", max_length=150)
    laboratorio: str = Field(default="Não informado", max_length=100)
    exige_receita: bool = Field(default=False)
    categorias: list[str] = Field(
        default_factory=list, 
        description="Categorias do medicamento (Ex: Genérico, Original, Controlados)"
    )

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

class CatalogoPageOut(BaseModel):
    """
    Schema para paginação do catálogo de produtos.
    """
    total: int
    limit: int
    offset: int
    items: list[CatalogoComOfertasOut]

class CatalogoFiltrosOut(BaseModel):
    """
    Schema de saída para os filtros dinâmicos do catálogo.
    """
    categorias: list[str]
    laboratorios: list[str]
    principios_ativos: list[str]

class HistoricoBase(BaseModel):
    """
    Schema base para o registro de histórico de preços.

    Define os dados fundamentais para rastreabilidade de valores, vinculando 
    o preço à farmácia e ao momento do registro.

    :param preco: Valor monetário do medicamento no momento da coleta.
    :type preco: decimal.Decimal
    :param data_registro: Data e hora em que o preço foi registrado no sistema.
    :type data_registro: datetime.datetime
    :param farmacia_id: Identificador da farmácia que pratica este preço.
    :type farmacia_id: int
    """
    preco: Decimal
    data_registro: datetime
    farmacia_id: int

class HistoricoOut(HistoricoBase):
    """
    Schema de saída para visualização do histórico de preços.

    Estende o schema base incluindo os identificadores únicos do registro 
    e do medicamento associado, permitindo a serialização direta do ORM.

    :param id: Identificador único do registro de histórico no banco de dados.
    :type id: int
    :param medicamento_id: Identificador do medicamento ao qual este preço pertence.
    :type medicamento_id: int
    """
    id: int
    medicamento_id: int

    model_config = ConfigDict(from_attributes=True)