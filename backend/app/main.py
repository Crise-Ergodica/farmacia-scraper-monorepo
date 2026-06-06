from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, catalogo, historico

app: FastAPI = FastAPI(title="Preço Bão API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalogo.router)
app.include_router(auth.router)
app.include_router(historico.router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "Aurora"}
