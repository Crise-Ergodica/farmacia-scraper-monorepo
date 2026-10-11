from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes.historico import get_medicine_history
from app.models.base import Base
from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.models.oferta_farmacia import OfertaFarmacia
from app.schemas.catalogo import CatalogoOut
from app.services.imagens import (
    image_rejection_reason,
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
    assert select_vtex_item_image(
        item, expected_ean="7891234567897", expected_sku="another-item"
    ) is None


@pytest.mark.asyncio
async def test_indiana_ean_lookup_uses_exact_item(monkeypatch):
    expected_ean = "7891234567897"
    requested = []

    class FakeResponse:
        content = b"[]"

        def raise_for_status(self):
            return None

        def json(self):
            return [{"productName": "Produto", "items": [
                {"itemId": "1", "ean": "7891234567890", "images": [
                    {"imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/other.jpg"}
                ]},
                {"itemId": "2", "ean": expected_ean, "images": [
                    {"imageUrl": "https://farmaciaindiana.vteximg.com.br/arquivos/produto-2.jpg"}
                ]},
            ]}]

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
    page = 'https://www.araujo.com.br/remedio/11151.html'
    html = '''<img src="/on/demandware.static/images/generico.webp">
      <meta property="og:image" content="https://i3-imagens-prd.araujo.com.br/webp/11151/121383_7896004734392_1.webp?sw=200&amp;sh=200">
    '''
    image = select_araujo_product_image(
        html, sku="ARJ11151", ean="7896004734392", product_url=page
    )
    assert image == "https://i3-imagens-prd.araujo.com.br/webp/11151/121383_7896004734392_1.webp?sw=200&sh=200"
    assert select_araujo_product_image(
        html, sku="ARJ11151", ean="7896004734393", product_url=page
    ) is None
    assert select_araujo_product_image(
        html, sku="ARJ1442", ean=None, product_url=page
    ) is None


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

    empty_period = get_medicine_history(product.id, "7d", pharmacy.id, db)
    assert empty_period.pharmacies == []
