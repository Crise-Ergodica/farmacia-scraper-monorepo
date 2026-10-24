from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes.catalogo import (
    ler_historico,
    obter_medicamento,
    redirecionar_imagem_catalogo,
)
from app.api.routes.historico import get_medicine_history
from app.models.base import Base
from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.models.oferta_farmacia import OfertaFarmacia
from app.schemas.catalogo import CatalogoOut
from app.schemas.oferta import OfertaOut
from app.services import imagens
from app.services.catalog_response import with_registry_images
from app.services.image_registry import upsert_image_reference
from app.services.imagens import (
    image_delivery_rejection_reason,
    image_rejection_reason,
    offer_image_delivery_rejection_reason,
    register_image_candidate,
    select_araujo_product_image,
    select_vtex_item_image,
    validate_image_association,
)
from app.services.preco_observacoes import registrar_observacao_preco
from scripts import processar_imagens


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(autouse=True)
def isolated_image_registry(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_REFERENCE_STORE_PATH", str(tmp_path / "images.json"))


def _register_external_image(
    product, url, *, offer=None, pharmacy_id=1, pharmacy="Test"
):
    assert upsert_image_reference(
        image_url=url,
        pharmacy_id=pharmacy_id,
        pharmacy=pharmacy,
        sku="test-sku",
        ean=product.codigo_barras,
        product_id="test-product",
        product_url="https://shop.example.test/item/p",
        catalog_id=product.id,
        offer_id=offer.id if offer is not None else None,
    )


def test_image_association_rejects_other_ean_and_generic_templates():
    url = "https://farmaciaindiana.vteximg.com.br/arquivos/7891234567890.jpg"
    valid, _, reason = validate_image_association(
        image_url=url,
        pharmacy_name="Indiana",
        sku="IND9988",
        ean="7891234567897",
        product_url="https://www.farmaciaindiana.com.br/item/p",
    )
    assert not valid
    assert "EAN" in (reason or "")
    assert image_rejection_reason(
        "https://www.araujo.com.br/on/demandware.static/tarjadoGenerico.svg"
    )
    assert image_rejection_reason(
        "https://www.araujo.com.br/on/demandware.static/images/generico.webp"
    )
    assert image_rejection_reason(
        "https://farmaciaindiana.vteximg.com.br/arquivos/"
        "MEDICAMENTO TARJADO GENERICO.jpg"
    )
    assert image_rejection_reason(
        "https://farmaciaindiana.vteximg.com.br/arquivos/"
        "CAIXA%20MEDICAMENTO%20v.2.0%20-%20CIMED.jpg"
    )
    assert image_rejection_reason(
        "https://i3-imagens-prd.araujo.com.br/webp/101392/231489_7897705203095_2.webp"
    )
    assert image_rejection_reason(
        "https://i3-imagens-prd.araujo.com.br/webp/7290/"
        "128666_7896026306751_1.webp?sw=200&sh=200&sm=fit"
    )
    assert image_rejection_reason(
        "https://farmaciaindiana.vteximg.com.br/arquivos/ids/306093/7896026306751.jpg"
    )
    assert image_rejection_reason(
        "https://i3-imagens-prd.araujo.com.br/webp/84977/120803_7898216367429_1.webp"
    )
    assert image_rejection_reason(
        "https://i3-imagens-prd.araujo.com.br/webp/167/128048_7896112486787_1.webp"
    )
    assert image_rejection_reason(
        "https://farmaciaindiana.vteximg.com.br/arquivos/ids/203063/7899547503845_0.jpg"
    )
    assert image_rejection_reason(
        "https://farmaciaindiana.vteximg.com.br/arquivos/ids/320348/"
        "lonium-40mg-30cpr.jpg"
    )


def test_offer_schema_allows_pharmacy_generic_for_its_product():
    generic_url = "https://i3-imagens-prd.araujo.com.br/webp/1/generico.webp"
    offer = OfertaOut(
        id=1,
        farmacia_id=1,
        catalogo_id=1,
        preco=Decimal("12.50"),
        quantidade_estoque=1,
        disponivel=True,
        url_origem="https://www.araujo.com.br/example/1.html",
        imagem_url=generic_url,
        farmacia_nome="Araujo",
        criado_em=datetime.now(),
    )
    assert offer.model_dump()["imagem_rejeitada"] is False
    assert offer.model_dump()["imagem_generica"] is True
    assert (
        offer_image_delivery_rejection_reason(
            generic_url, offer.url_origem, offer.farmacia_nome
        )
        is None
    )
    assert offer_image_delivery_rejection_reason(
        "https://i3-imagens-prd.araujo.com.br/webp/2/generico.webp",
        offer.url_origem,
        offer.farmacia_nome,
    )


def test_generic_catalog_image_reference_does_not_depend_on_audit_status():
    url = "https://farmaciaindiana.vteximg.com.br/arquivos/CAIXA-MEDICAMENTO.jpg"
    product = CatalogoOut(
        id=77,
        name_search="Medicamento teste",
        criado_em=datetime.now(),
        imagem_url=url,
        imagem_status="pendente",
    )
    assert (
        product.imagem_ref
        == "/catalogo/medicamentos/77/imagem?v="
        + sha256(url.encode("utf-8")).hexdigest()[:12]
    )
    assert image_delivery_rejection_reason(url) is None
    assert image_rejection_reason(url)


def test_catalog_image_endpoint_requires_same_catalog_sku_or_matching_ean(db):
    pharmacy = Farmacia(
        cnpj="12345678901234",
        razao_social="Farmacia teste",
        nome_fantasia="Indiana",
        endereco_completo="Local",
    )
    product = CatalogoBase(
        name_search="Medicamento teste",
        imagem_url="https://farmaciaindiana.vteximg.com.br/arquivos/CAIXA-MEDICAMENTO.jpg",
        imagem_sku_origem="IND-77",
        imagem_status="pendente",
    )
    db.add_all([pharmacy, product])
    db.flush()
    offer = OfertaFarmacia(
        sku_interno="IND-77",
        preco=Decimal("10.00"),
        quantidade_estoque=1,
        disponivel=True,
        url_origem="https://www.farmaciaindiana.com.br/produto/p",
        farmacia_id=pharmacy.id,
        catalogo_id=product.id,
    )
    db.add(offer)
    db.flush()
    _register_external_image(
        product, product.imagem_url, offer=offer, pharmacy="Indiana"
    )

    response = redirecionar_imagem_catalogo(product.id, db)
    assert response.status_code == 302
    assert response.headers["location"] == product.imagem_url

    product.imagem_sku_origem = "IND-OTHER"
    db.flush()
    response = redirecionar_imagem_catalogo(product.id, db)
    assert response.status_code == 302  # PostgreSQL image metadata is not consulted.


def test_catalog_response_uses_external_registry_and_hides_legacy_offer_url(db):
    pharmacy = Farmacia(
        cnpj="22345678901234",
        razao_social="Farmacia teste",
        nome_fantasia="Indiana",
        endereco_completo="Local",
    )
    product = CatalogoBase(
        name_search="Produto de teste",
        imagem_url="https://legacy.example.test/old.jpg",
    )
    db.add_all([pharmacy, product])
    db.flush()
    offer = OfertaFarmacia(
        sku_interno="IND-88",
        preco=Decimal("12.00"),
        quantidade_estoque=1,
        disponivel=True,
        url_origem="https://www.farmaciaindiana.com.br/produto/p",
        imagem_url="https://legacy.example.test/old-offer.jpg",
        farmacia_id=pharmacy.id,
        catalogo_id=product.id,
    )
    db.add(offer)
    db.flush()
    external_url = "https://cdn.example.test/registry.jpg"
    _register_external_image(product, external_url, offer=offer, pharmacy="Indiana")

    result = with_registry_images(product)

    assert result.imagem_urls == [external_url]
    assert result.imagem_url == external_url
    assert result.ofertas[0].imagem_url is None


def test_catalog_generic_image_can_match_recorded_araujo_sku_without_offer(db):
    product = CatalogoBase(
        codigo_barras="7896026307925",
        name_search="Glyxambi 25mg + 5mg",
        imagem_url=(
            "https://i3-imagens-prd.araujo.com.br/webp/7290/"
            "128666_7896026306751_1.webp?sw=200&sh=200"
        ),
        imagem_fonte="Araujo",
        imagem_sku_origem="ARJ7290",
        imagem_match="catalog_duplicate",
        imagem_status="pendente",
    )
    db.add(product)
    db.flush()

    _register_external_image(product, product.imagem_url, pharmacy="Araujo")
    response = redirecionar_imagem_catalogo(product.id, db)
    assert response.status_code == 302
    assert response.headers["location"] == product.imagem_url

    product.imagem_url = product.imagem_url.replace("/7290/", "/7291/")
    db.flush()
    response = redirecionar_imagem_catalogo(product.id, db)
    assert response.headers["location"] == (
        "https://i3-imagens-prd.araujo.com.br/webp/7290/"
        "128666_7896026306751_1.webp?sw=200&sh=200"
    )


def test_catalog_image_can_match_recorded_indiana_sku_without_ean_or_offer(db):
    product = CatalogoBase(
        name_search="Kit Allegra e Novalgina",
        imagem_url=(
            "https://farmaciaindiana.vteximg.com.br/arquivos/ids/379046/"
            "kit-allegra-180mg-10-comprimidos-novalgina-1g-20-comprimidos.jpg"
        ),
        imagem_fonte="Indiana",
        imagem_sku_origem="IND12401682",
        imagem_match="catalog_duplicate",
        imagem_status="pendente",
    )
    db.add(product)
    db.flush()

    _register_external_image(product, product.imagem_url, pharmacy="Indiana")
    response = redirecionar_imagem_catalogo(product.id, db)
    assert response.status_code == 302
    assert response.headers["location"] == product.imagem_url


@pytest.mark.parametrize(
    ("url", "catalog_ean", "image_ean", "sku", "match"),
    [
        (
            "https://farmaciaindiana.vteximg.com.br/arquivos/ids/212425/7896830500147_0.jpg",
            "7897406119886",
            "7897406119886",
            "IND13725",
            "ean",
        ),
        (
            "https://farmaciaindiana.vteximg.com.br/arquivos/ids/283783/Imagem.jpg?v=638267801085470000",
            None,
            "7896006221088",
            "IND169625",
            "ean",
        ),
    ],
)
def test_catalog_image_accepts_recorded_product_ean_or_generic_sku_lineage(
    db, url, catalog_ean, image_ean, sku, match
):
    product = CatalogoBase(
        codigo_barras=catalog_ean,
        name_search="Produto de origem Indiana",
        imagem_url=url,
        imagem_fonte="Indiana",
        imagem_sku_origem=sku,
        imagem_ean=image_ean,
        imagem_match=match,
        imagem_status="pendente",
    )
    db.add(product)
    db.flush()
    _register_external_image(product, url, pharmacy="Indiana")

    response = redirecionar_imagem_catalogo(product.id, db)

    assert response.status_code == 302
    assert response.headers["location"] == url


def test_scraper_keeps_offer_generic_image_without_requiring_audit_approval():
    product = CatalogoBase(name_search="Medicamento genérico da oferta")
    url = "https://farmaciaindiana.vteximg.com.br/arquivos/CAIXA-MEDICAMENTO.jpg"

    stored = register_image_candidate(
        product,
        image_url=url,
        pharmacy_name="Indiana",
        sku="IND9988",
        ean="7891234567897",
        product_url="https://www.farmaciaindiana.com.br/produto/item/p",
    )

    assert stored
    assert product.imagem_url == url
    assert product.imagem_fonte == "Indiana"
    assert product.imagem_match == "sku"
    assert product.imagem_status == "pendente"


def test_scraper_records_exact_vtex_item_identity_when_filename_ean_is_legacy():
    product = CatalogoBase(
        codigo_barras="7891058167073",
        name_search="Allegra 60mg 10 comprimidos",
    )
    url = "https://farmaciaindiana.vteximg.com.br/arquivos/7891058024314-1.jpg"

    stored = register_image_candidate(
        product,
        image_url=url,
        pharmacy_name="Indiana",
        sku="IND11541",
        ean="7891058167073",
        product_url="https://www.farmaciaindiana.com.br/allegra-60mg-10-capsulas/p",
        identity_confirmed=True,
    )

    assert stored
    assert product.imagem_match == "sku_item"
    assert product.codigo_barras == "7891058167073"


def test_vtex_exact_item_accepts_its_generic_image():
    item = {
        "itemId": "122816",
        "ean": "7896026307925",
        "images": [
            {
                "imageUrl": (
                    "https://farmaciaindiana.vteximg.com.br/arquivos/"
                    "MEDICAMENTO-TARJADO-GENERICO.jpg"
                )
            }
        ],
    }

    assert (
        select_vtex_item_image(
            item, expected_ean="7896026307925", expected_sku="122816"
        )
        == item["images"][0]["imageUrl"]
    )


@pytest.mark.parametrize(
    ("ean", "image_url", "source"),
    [
        (
            "7898560666865",
            "https://farmaciamodelo.com.br/BACKOFFICE/Uploads/Produto/Normal/2_fml_.jpg",
            "FarmaciaModelo",
        ),
        (
            "7898581711254",
            "https://www.farmaciasnissei.com.br/media/medicamentos/caixa-medicamento-geral-tarja-vermelha.webp",
            "Nissei",
        ),
    ],
)
def test_trusted_external_product_image_uses_exact_recorded_ean(
    db, ean, image_url, source
):
    product = CatalogoBase(
        codigo_barras=ean,
        name_search="Medicamento identificado por EAN",
        imagem_url=image_url,
        imagem_fonte=source,
        imagem_ean=ean,
        imagem_match="ean",
        imagem_status="pendente",
    )
    db.add(product)
    db.flush()
    _register_external_image(product, image_url, pharmacy=source)

    response = redirecionar_imagem_catalogo(product.id, db)

    assert response.status_code == 302
    assert response.headers["location"] == image_url


@pytest.mark.asyncio
async def test_image_verifier_accepts_generic_content_hash(monkeypatch):
    data = b"RIFF\x14\x00\x00\x00WEBP" + b"generic-test-data"
    digest = sha256(data).hexdigest()
    monkeypatch.setattr(imagens, "KNOWN_GENERIC_CONTENT_HASHES", {digest})
    actual_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200, headers={"content-type": "image/webp"}, content=data
            )
        )
        return actual_client(*args, transport=transport, **kwargs)

    monkeypatch.setattr(imagens.httpx, "AsyncClient", mocked_client)
    result = await imagens.verify_image_url(
        "https://i3-imagens-prd.araujo.com.br/webp/123/product.webp"
    )
    assert result.ok
    assert result.content_sha256 == digest


@pytest.mark.asyncio
async def test_image_verifier_accepts_known_generic_url(monkeypatch):
    data = b"RIFF\x14\x00\x00\x00WEBP" + b"generic-url-data"
    url = next(iter(imagens.KNOWN_GENERIC_URLS))
    actual_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200, headers={"content-type": "image/webp"}, content=data
            )
        )
        return actual_client(*args, transport=transport, **kwargs)

    monkeypatch.setattr(imagens.httpx, "AsyncClient", mocked_client)
    result = await imagens.verify_image_url(url)
    assert result.ok


def test_vtex_selects_matching_alternative_image():
    item = {
        "itemId": "9988",
        "ean": "7891234567897",
        "images": [
            {
                "imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/7891234567890.jpg"
            },
            {
                "imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/item-9988.webp"
            },
        ],
    }
    assert (
        select_vtex_item_image(item, expected_ean="7891234567897")
        == item["images"][1]["imageUrl"]
    )
    assert select_vtex_item_image(item, expected_ean="7890000000000") is None
    assert (
        select_vtex_item_image(
            item, expected_ean="7891234567897", expected_sku="another-item"
        )
        is None
    )


def test_vtex_allows_other_filename_ean_only_for_exact_item_identity():
    item = {
        "itemId": "47276",
        "ean": "7896015521684",
        "images": [
            {
                "imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/7896015521646.jpg"
            }
        ],
    }
    assert (
        select_vtex_item_image(item, expected_ean="7896015521684", expected_sku="47276")
        == item["images"][0]["imageUrl"]
    )
    assert (
        select_vtex_item_image(
            item, expected_ean="7896015521684", expected_sku="wrong-sku"
        )
        is None
    )


def test_ean13_matches_gtin14_with_leading_zero():
    assert imagens.gtin_matches("7899547531213", "07899547531213")
    assert not imagens.gtin_matches("7899547531213", "07899547531214")


@pytest.mark.asyncio
async def test_indiana_ean_lookup_uses_exact_item(monkeypatch):
    expected_ean = "7891234567897"
    requested = []

    class FakeResponse:
        content = b"[]"

        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "productName": "Produto",
                    "items": [
                        {
                            "itemId": "1",
                            "ean": "7891234567890",
                            "images": [
                                {
                                    "imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/other.jpg"
                                }
                            ],
                        },
                        {
                            "itemId": "2",
                            "ean": expected_ean,
                            "images": [
                                {
                                    "imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/produto-2.jpg"
                                }
                            ],
                        },
                    ],
                }
            ]

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, url, *, params):
            requested.append((url, params))
            return FakeResponse()

    monkeypatch.setattr(
        processar_imagens.httpx, "AsyncClient", lambda **_: FakeClient()
    )
    record = await processar_imagens.lookup_indiana_ean(expected_ean, {})
    assert requested[0][1] == {"fq": f"alternateIds_Ean:{expected_ean}"}
    assert record["sku"] == "2"
    assert record["item"]["ean"] == expected_ean


def test_araujo_product_page_uses_exact_sku_photo_after_generic_thumbnail():
    page = "https://www.araujo.com.br/azelan-gel-com-30g/69045.html"
    html = """<img src="/on/demandware.static/images/generico.webp">
      <meta property="og:image" content="https://i3-imagens-prd.araujo.com.br/redimensionada/380x380/69045/07898916010052_4.webp?sw=200&amp;sh=200">
    """
    image = select_araujo_product_image(
        html, sku="ARJ69045", ean=None, product_url=page
    )
    assert (
        image
        == "https://i3-imagens-prd.araujo.com.br/redimensionada/380x380/69045/07898916010052_4.webp?sw=200&sh=200"
    )
    assert (
        select_araujo_product_image(
            html, sku="ARJ11151", ean="7896004734393", product_url=page
        )
        is None
    )
    assert (
        select_araujo_product_image(html, sku="ARJ1442", ean=None, product_url=page)
        is None
    )


def test_image_reference_changes_when_source_photo_changes():
    base = dict(
        id=9,
        name_search="Nimesulida",
        criado_em=datetime.now(),
        imagem_status="verificada",
    )
    first = CatalogoOut(
        **base, imagem_url="https://farmaciaindiana.vteximg.com.br/arquivos/1.jpg"
    )
    second = CatalogoOut(
        **base, imagem_url="https://i3-imagens-prd.araujo.com.br/webp/9/2.webp"
    )
    assert first.imagem_ref != second.imagem_ref
    assert first.imagem_ref.startswith("/catalogo/medicamentos/9/imagem?v=")


def test_price_history_only_records_changes_and_period_endpoint_filters(db):
    product = CatalogoBase(name_search="Produto teste")
    pharmacy = Farmacia(
        cnpj="12345678901234",
        razao_social="Farmácia teste",
        nome_fantasia="Teste",
        endereco_completo="Local",
    )
    db.add_all([product, pharmacy])
    db.flush()
    offer = OfertaFarmacia(
        sku_interno="TESTE1",
        preco=Decimal("10.00"),
        quantidade_estoque=1,
        disponivel=True,
        url_origem="https://farmacia.example/product",
        farmacia_id=pharmacy.id,
        catalogo_id=product.id,
    )
    db.add(offer)
    db.flush()
    now = datetime.now() - timedelta(days=10)
    event = registrar_observacao_preco(
        offer,
        preco=Decimal("10.00"),
        observado_em=now,
        origem="teste",
        farmacia_id=pharmacy.id,
        medicamento_id=product.id,
        preco_anterior=None,
    )
    db.add(event)
    assert (
        registrar_observacao_preco(
            offer,
            preco=Decimal("10.00"),
            observado_em=now + timedelta(days=1),
            origem="teste",
            farmacia_id=pharmacy.id,
            medicamento_id=product.id,
            preco_anterior=Decimal("10.00"),
        )
        is None
    )
    changed = registrar_observacao_preco(
        offer,
        preco=Decimal("9.00"),
        observado_em=now + timedelta(days=2),
        origem="teste",
        farmacia_id=pharmacy.id,
        medicamento_id=product.id,
        preco_anterior=Decimal("10.00"),
    )
    db.add(changed)
    db.commit()

    response = get_medicine_history(product.id, "all", None, db)
    assert len(response.pharmacies[0].history) == 2
    assert response.statistics[pharmacy.id].menor_preco == Decimal("9.00")
    assert response.statistics[pharmacy.id].variacao_absoluta == Decimal("-1.00")
    assert offer.observado_em == now + timedelta(days=2)
    assert event.data_registro == now

    empty_period = get_medicine_history(product.id, "7d", pharmacy.id, db)
    assert empty_period.pharmacies == []
    assert empty_period.total_observacoes == 2


def test_price_observation_rejects_invalid_zero_without_mutating_offer(db):
    offer = OfertaFarmacia(
        sku_interno="VALID-PRICE",
        preco=Decimal("10.79"),
        quantidade_estoque=1,
        disponivel=True,
        url_origem="https://farmacia.example/valid-price",
        farmacia_id=1,
        catalogo_id=1,
    )
    event = registrar_observacao_preco(
        offer,
        preco=Decimal("0"),
        observado_em=datetime.now(),
        origem="teste",
        farmacia_id=1,
        medicamento_id=1,
        preco_anterior=Decimal("10.79"),
    )

    assert event is None
    assert offer.preco == Decimal("10.79")
    assert offer.observado_em is None


def test_history_keeps_initial_pharmacy_observations_and_unavailable_offers(db):
    product = CatalogoBase(name_search="Produto com duas farmácias")
    indiana = Farmacia(
        cnpj="11111111111111",
        razao_social="Indiana Ltda",
        nome_fantasia="Indiana",
        endereco_completo="Local 1",
    )
    pacheco = Farmacia(
        cnpj="22222222222222",
        razao_social="Drogarias Pacheco Ltda",
        nome_fantasia="Pacheco",
        endereco_completo="Local 2",
    )
    db.add_all([product, indiana, pacheco])
    db.flush()
    first_at = datetime(2026, 9, 1, 12, 0)
    offers = [
        OfertaFarmacia(
            sku_interno="IND-1",
            preco=Decimal("10.00"),
            quantidade_estoque=1,
            disponivel=True,
            url_origem="https://indiana.example/item",
            farmacia_id=indiana.id,
            catalogo_id=product.id,
        ),
        OfertaFarmacia(
            sku_interno="PCH-1",
            preco=Decimal("12.00"),
            quantidade_estoque=0,
            disponivel=False,
            url_origem="https://pacheco.example/item",
            farmacia_id=pacheco.id,
            catalogo_id=product.id,
        ),
    ]
    db.add_all(offers)
    db.flush()
    for offer, pharmacy, price in zip(offers, [indiana, pacheco], ["10.00", "12.00"]):
        event = registrar_observacao_preco(
            offer,
            preco=Decimal(price),
            observado_em=first_at,
            origem=pharmacy.nome_fantasia,
            farmacia_id=pharmacy.id,
            medicamento_id=product.id,
            preco_anterior=None,
        )
        assert event is not None
        db.add(event)
    db.commit()

    response = get_medicine_history(product.id, "all", None, db)
    assert response.total_observacoes == 2
    assert {item.pharmacy_name for item in response.pharmacies} == {
        "Indiana",
        "Pacheco",
    }
    assert all(len(item.history) == 1 for item in response.pharmacies)
    assert all(
        item.history[0].data_registro.tzinfo is not None for item in response.pharmacies
    )
    assert response.statistics[pacheco.id].primeiro_preco == Decimal("12.00")

    legacy_events = ler_historico(product.id, db)
    assert len(legacy_events) == 2
    assert all(event.medicamento_id == product.id for event in legacy_events)


def test_medicine_detail_returns_current_offers_from_indiana_and_pacheco(db):
    product = CatalogoBase(name_search="Medicamento em Indiana e Pacheco")
    indiana = Farmacia(
        cnpj="33333333333333",
        razao_social="Indiana Ltda",
        nome_fantasia="Indiana",
        endereco_completo="Local 1",
    )
    pacheco = Farmacia(
        cnpj="44444444444444",
        razao_social="Drogarias Pacheco Ltda",
        nome_fantasia="Pacheco",
        endereco_completo="Local 2",
    )
    db.add_all([product, indiana, pacheco])
    db.flush()
    db.add_all(
        [
            OfertaFarmacia(
                sku_interno="IND-TEST-1",
                preco=Decimal("20.28"),
                quantidade_estoque=1,
                disponivel=True,
                url_origem="https://indiana.example/medicine",
                farmacia_id=indiana.id,
                catalogo_id=product.id,
            ),
            OfertaFarmacia(
                sku_interno="PCH-TEST-1",
                preco=Decimal("14.99"),
                quantidade_estoque=1,
                disponivel=True,
                url_origem="https://pacheco.example/medicine",
                farmacia_id=pacheco.id,
                catalogo_id=product.id,
            ),
        ]
    )
    db.commit()

    detail = obter_medicamento(product.id, db)

    offers_by_pharmacy = {offer.farmacia_nome: offer.preco for offer in detail.ofertas}
    assert offers_by_pharmacy == {
        "Indiana": Decimal("20.28"),
        "Pacheco": Decimal("14.99"),
    }
