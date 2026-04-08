"""
Ponto de entrada do pacote de schemas (Pydantic) para centralização de exportações.

Este módulo inicializa a camada de validação e transferência de dados (DTOs) da 
aplicação. Ele expõe publicamente os contratos de entrada (Base) e saída (Out) 
relacionados ao catálogo de produtos e às ofertas locais de cada farmácia, 
garantindo que os endpoints do FastAPI tenham acesso rápido e centralizado 
a todas as estruturas de serialização necessárias para o frontend.
"""

from .catalogo import CatalogoBaseSchema, CatalogoOut, CatalogoComOfertasOut
from .oferta import OfertaBaseSchema, OfertaOut

__all__ = [
    # Schemas do Catálogo Global (Dados Estáticos)
    "CatalogoBaseSchema",
    "CatalogoOut",
    
    # Schemas de Oferta (Precificação, Estoque e Lojas Locais)
    "OfertaBaseSchema",
    "OfertaOut",
    
    # Schemas Agregados (Junção de Domínios para o Frontend)
    "CatalogoComOfertasOut",
]