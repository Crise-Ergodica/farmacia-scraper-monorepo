from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import catalogo

app: FastAPI = FastAPI(title="Preço Bão API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalogo.router)

@app.get("/") 
def read_root() -> dict[str, str]:
    """
    Root endpoint to verify the API status.

    Returns
    -------
    dict[str, str]
        A basic welcome message.
    """
    return {"Hello": "Aurora"}