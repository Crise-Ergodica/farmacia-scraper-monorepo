import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import usuarios, catalogo, historico


def _get_cors_origins() -> list[str]:
    """Retrieves the CORS origins from environment variables.

    Reads the `BACKEND_CORS_ORIGINS` environment variable, attempting to parse
    it as a JSON list of strings. If the variable is not set, or if parsing
    fails, an empty list is returned.

    Returns:
        list[str]: A list of allowed CORS origins.
    """
    origins_env = os.environ.get("BACKEND_CORS_ORIGINS")
    if origins_env:
        try:
            parsed = json.loads(origins_env)
            if isinstance(parsed, list):
                return [str(origin) for origin in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
    return []


app: FastAPI = FastAPI(title="Preço Bão API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalogo.router)
app.include_router(usuarios.router)
app.include_router(historico.router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "Aurora"}
