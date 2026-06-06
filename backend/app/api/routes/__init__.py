from .auth import router as auth_router
from .catalogo import router as catalogo_router
from .historico import router as historico_router

__all__ = ["auth_router", "catalogo_router", "historico_router"]
