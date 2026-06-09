"""
Ponto de entrada do pacote de schemas (Pydantic) para centralização de exportações.

Este módulo inicializa a camada de validação e transferência de dados (DTOs) da 
aplicação. Ele expõe publicamente os contratos de entrada (Base) e saída (Out) 
relacionados ao catálogo de produtos, às ofertas locais e ao rastreamento 
temporal de preços (histórico), garantindo que os endpoints do FastAPI tenham 
acesso rápido e centralizado a todas as estruturas de serialização necessárias.
"""

from .catalogo import CatalogoBaseSchema, CatalogoOut, CatalogoComOfertasOut, CatalogoPageOut, CatalogoFiltrosOut, HistoricoBase, HistoricoOut
from .oferta import OfertaBaseSchema, OfertaOut
from .historico import PricePointSchema, PharmacyHistorySchema, MedicineHistoryResponse

__all__ = [
    # Schemas do Catálogo Global (Dados Estáticos)
    "CatalogoBaseSchema",
    "CatalogoOut",
    
    # Schemas de Oferta (Precificação, Estoque e Lojas Locais)
    "OfertaBaseSchema",
    "OfertaOut",

    # Schemas de Histórico (Rastreabilidade de Preços no Tempo)
    "HistoricoBase",
    "HistoricoOut",
    "PricePointSchema",
    "PharmacyHistorySchema",
    "MedicineHistoryResponse",
    
    # Schemas Agregados (Junção de Domínios para o Frontend)
    "CatalogoComOfertasOut",
    "CatalogoPageOut",
    "CatalogoFiltrosOut",
]
