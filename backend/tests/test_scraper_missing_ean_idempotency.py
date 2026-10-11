from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.catalogo import CatalogoBase
from app.models.oferta_farmacia import OfertaFarmacia
from app.schemas.oferta import ProdutoExtraidoSchema
from app.scrapers import base as base_module
from app.scrapers import indiana as indiana_module

ENRICHED = {
    "principio_ativo": "Não informado",
    "laboratorio": "Não informado",
    "exige_receita": False,
    "categorias": [],
}


def test_base_scraper_reuses_missing_ean_offer_by_sku_and_url(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(base_module, "SessionLocal", factory)
    monkeypatch.setattr(
        base_module.ServicoEnriquecimentoFarmacologico,
        "enriquecer_lote",
        staticmethod(lambda _db, batch: batch),
    )

    class Scraper(base_module.BasePharmacyScraper):
        async def extrair_catalogo(self):
            return None

    scraper = Scraper("12345678000100", "Farmácia Teste", "Teste", "Local")
    product = ProdutoExtraidoSchema(
        id="sku-1",
        sku_interno="SKU-1",
        ean=None,
        name_search="Produto sem EAN",
        preco=12.5,
        link="https://farmacia.example/produto/sku-1",
    )
    batch = [{"validado": product, "enriquecido": ENRICHED}]

    scraper._processar_e_salvar_lote(batch)
    scraper._processar_e_salvar_lote(batch)

    with factory() as db:
        assert db.query(CatalogoBase).count() == 1
        assert db.query(OfertaFarmacia).count() == 1
        assert db.query(CatalogoBase).one().codigo_barras is None
    engine.dispose()


def test_indiana_scraper_reuses_missing_ean_offer_by_sku_and_url(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(indiana_module, "SessionLocal", factory)
    monkeypatch.setattr(
        indiana_module.ServicoEnriquecimentoFarmacologico,
        "enriquecer_produto",
        staticmethod(lambda *_args: ENRICHED),
    )
    product = {
        "id": "sku-2",
        "sku_interno": "IND12345",
        "ean": None,
        "name_search": "Produto Indiana sem EAN",
        "preco": 8.75,
        "link": "https://www.farmaciaindiana.com.br/produto/sku-2/p",
    }

    indiana_module.salvar_no_banco([product])
    indiana_module.salvar_no_banco([product])

    with factory() as db:
        assert db.query(CatalogoBase).count() == 1
        assert db.query(OfertaFarmacia).count() == 1
        offer = db.query(OfertaFarmacia).one()
        assert offer.sku_interno == "IND12345"
        assert offer.preco == Decimal("8.75")
        assert db.query(CatalogoBase).one().codigo_barras is None
    engine.dispose()
