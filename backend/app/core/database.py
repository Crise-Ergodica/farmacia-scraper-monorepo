"""
app.core.database
-----------------
Gerenciamento de conexões com o banco de dados e rotinas de persistência.
"""

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configuração do Motor e Fábrica de Sessões
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Erro Crítico: DATABASE_URL não encontrada.")

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
