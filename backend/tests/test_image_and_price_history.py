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
from app.services.imagens import (
    image_rejection_reason,
    select_vtex_item_image,
    validate_image_association,
)
from app.services.preco_observacoes import registrar_observacao_preco


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
