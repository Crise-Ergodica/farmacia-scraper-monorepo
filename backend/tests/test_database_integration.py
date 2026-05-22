import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DataError
from app.models.base import Base
from app.models.catalogo import CatalogoBase
from app.models.oferta_farmacia import OfertaFarmacia

# Use uma string de conexão mock ou a do docker se estiver rodando
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://aurora_admin:super_senha_segura@localhost:5432/farmacia_db"

@pytest.fixture(scope="module")
def engine():
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        pytest.skip(f"Banco de dados nao disponivel: {e}")

@pytest.fixture(scope="function")
def db_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_insercao_ean_invalido_maior_que_14_gera_data_error(db_session):
    # EAN com 15 caracteres deve quebrar no limit da db
    produto = CatalogoBase(
        codigo_barras="123456789012345",
        name_search="Produto Teste Limite EAN",
        principio_ativo="Teste",
        laboratorio="Teste",
        exige_receita=False
    )
    db_session.add(produto)

    with pytest.raises(DataError) as exc:
        db_session.commit()

    assert "value too long for type character varying(14)" in str(exc.value)

def test_insercao_ean_nulo_sucesso(db_session):
    # EAN nulo deve ser aceito dado o nullable=True
    produto = CatalogoBase(
        codigo_barras=None,
        name_search="Produto Teste EAN Nulo",
        principio_ativo="Teste",
        laboratorio="Teste",
        exige_receita=False
    )
    db_session.add(produto)
    db_session.commit()

    # Valida que inseriu e gerou id
    assert produto.id is not None
    assert produto.codigo_barras is None

def test_insercao_oferta_sem_sku_interno_gera_erro(db_session):
    from sqlalchemy.exc import IntegrityError

    # Cria produto base primeiro para nao violar fk do catalogo
    produto = CatalogoBase(
        codigo_barras="1234567890123",
        name_search="Produto Teste Oferta",
        principio_ativo="Teste",
        laboratorio="Teste",
        exige_receita=False
    )
    db_session.add(produto)
    db_session.commit()

    # Cria OfertaFarmacia sem informar o sku_interno (que eh nullable=False)
    # Ignora o farmacia_id pois o IntegrityError de not null do sku_interno deve barrar antes (ou junto)
    oferta = OfertaFarmacia(
        preco=10.50,
        quantidade_estoque=1,
        disponivel=True,
        url_origem="http://test.com",
        farmacia_id=1,
        catalogo_id=produto.id
    )

    db_session.add(oferta)
    with pytest.raises(IntegrityError) as exc:
        db_session.commit()

    assert "null value in column \"sku_interno\"" in str(exc.value)