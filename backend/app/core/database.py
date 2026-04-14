"""
app.core.database
-----------------
Gerenciamento de conexões com o banco de dados e rotinas de persistência.
"""
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Generator

# from app.models.farmacia import Farmacia
from app.models import OfertaFarmacia, CatalogoBase, Farmacia
from app.core.utils import validar_ean13

# Configuração do Motor e Fábrica de Sessões
DATABASE_URL = "postgresql+psycopg2://aurora_admin:super_senha_segura@localhost:4242/farmacia_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Gerador de dependência do FastAPI para sessões de banco de dados.
    Garante a abertura e o fechamento seguro das conexões por requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()