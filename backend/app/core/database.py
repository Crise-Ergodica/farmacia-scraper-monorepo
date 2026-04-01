"""
app.core.database
-----------------
Gerenciamento de conexões com o banco de dados e rotinas de persistência.
"""
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.models.farmacia import Farmacia
from app.models.medicamento import Medicamento
from app.core.utils import validar_ean13

# Configuração do Motor e Fábrica de Sessões
DATABASE_URL = "postgresql+psycopg2://aurora_admin:super_senha_segura@localhost:4242/farmacia_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def salvar_no_banco(produtos: List[Dict[str, Any]]) -> None:
    """
    Persiste uma lista de produtos no banco de dados.
    Atualiza o preço caso o medicamento (EAN) já exista.
    """
    db = SessionLocal()
    
    try:
        cnpj_padrao = "00000000000100"
        farmacia = db.query(Farmacia).filter(Farmacia.cnpj == cnpj_padrao).first()

        if not farmacia:
            farmacia = Farmacia(
                cnpj=cnpj_padrao,
                razao_social="Farmácia Indiana - Web Scraper",
                nome_fantasia="Indiana",
                endereco_completo="Extração API REST"
            )
            db.add(farmacia)
            db.commit()
            db.refresh(farmacia)

        for prod in produtos:
            ean = prod.get('ean')

            if not ean or not validar_ean13(ean):
                continue

            medicamento_existente = db.query(Medicamento).filter(Medicamento.codigo_barras == ean).first()

            if not medicamento_existente:
                novo_med = Medicamento(
                    codigo_barras=ean,
                    nome=prod['nome'],
                    preco=prod['preco'],
                    url_origem=prod['link'],
                    principio_ativo="Não informado",
                    laboratorio="Não informado",
                    farmacia_id=farmacia.id
                )
                db.add(novo_med)
            else:
                medicamento_existente.preco = prod['preco']
                medicamento_existente.url_origem = prod['link']

        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[ERRO DB] Falha na persistência: {e}")
    finally:
        db.close()