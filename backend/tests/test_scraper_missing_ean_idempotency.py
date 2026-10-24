import json
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


def test_base_scraper_stores_image_reference_outside_postgres(monkeypatch, tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(base_module, "SessionLocal", factory)
    registry_path = tmp_path / "references.json"
    monkeypatch.setenv("IMAGE_REFERENCE_STORE_PATH", str(registry_path))
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
        imagem_url="https://images.example.test/products/package.jpg",
    )
    batch = [{"validado": product, "enriquecido": ENRICHED}]

    scraper._processar_e_salvar_lote(batch)
    scraper._processar_e_salvar_lote(batch)

    with factory() as db:
        assert db.query(CatalogoBase).count() == 1
        assert db.query(OfertaFarmacia).count() == 1
        assert db.query(CatalogoBase).one().codigo_barras is None
        assert db.query(CatalogoBase).one().imagem_url is None
        assert db.query(OfertaFarmacia).one().imagem_url is None
    reference = json.loads(registry_path.read_text(encoding="utf-8"))["records"][0]
    assert reference["image_url"] == product.imagem_url
    assert reference["sku"] == "SKU-1"
    engine.dispose()


def test_indiana_scraper_stores_image_reference_outside_postgres(monkeypatch, tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(indiana_module, "SessionLocal", factory)
    registry_path = tmp_path / "indiana-references.json"
    monkeypatch.setenv("IMAGE_REFERENCE_STORE_PATH", str(registry_path))
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
        "imagem_url": "https://farmaciaindiana.vteximg.com.br/arquivos/package.jpg",
    }

    indiana_module.salvar_no_banco([product])
    indiana_module.salvar_no_banco([product])

    with factory() as db:
        assert db.query(CatalogoBase).count() == 1
        assert db.query(OfertaFarmacia).count() == 1
        offer = db.query(OfertaFarmacia).one()
        assert offer.sku_interno == "IND12345"
        assert offer.preco == Decimal("8.75")
        assert offer.imagem_url is None
        assert db.query(CatalogoBase).one().codigo_barras is None
        assert db.query(CatalogoBase).one().imagem_url is None
    reference = json.loads(registry_path.read_text(encoding="utf-8"))["records"][0]
    assert reference["image_url"] == product["imagem_url"]
    assert reference["offer_id"] == offer.id
    engine.dispose()
