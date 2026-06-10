from .usuarios import router as usuarios_router
from .catalogo import router as catalogo_router
from .historico import router as historico_router

__all__ = ["usuarios_router", "catalogo_router", "historico_router"]
