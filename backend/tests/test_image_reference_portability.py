"""Tests for safe and idempotent image-reference portability."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, CatalogoBase, Farmacia, OfertaFarmacia
from app.services.image_reference_portability import (
    export_image_references,
    import_image_references,
)
from app.services.imagens import validate_image_association

IMAGE_URL = "https://farmaciaindiana.vteximg.com.br/arquivos/caixa-azul.jpg"
PRODUCT_URL = "https://www.farmaciaindiana.com.br/produto-teste/p"


def _product(name: str, ean: str | None = None) -> CatalogoBase:
    return CatalogoBase(
        codigo_barras=ean,
        name_search=name,
        principio_ativo="Não informado",
        laboratorio="Não informado",
        exige_receita=False,
        categorias=[],
    )


def _offer(product: CatalogoBase, pharmacy: Farmacia) -> OfertaFarmacia:
    return OfertaFarmacia(
        sku_interno="IND123",
        preco="1.00",
        quantidade_estoque=1,
        disponivel=True,
        url_origem=PRODUCT_URL,
        imagem_url=IMAGE_URL,
        farmacia=pharmacy,
        produto_catalogo=product,
    )


def _database() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def _farmacia(db: Session) -> Farmacia:
    pharmacy = Farmacia(
        cnpj="12345678000199",
        razao_social="Farmácia Teste Ltda.",
        nome_fantasia="Indiana",
        telefone=None,
        endereco_completo="Local de teste",
    )
    db.add(pharmacy)
    db.flush()
    return pharmacy


def test_export_import_uses_stable_identity_and_is_idempotent() -> None:
    source = _database()
    source_pharmacy = _farmacia(source)
    source_product = _product("Produto com EAN", "7891234567895")
    source_product.imagem_url = IMAGE_URL
    source_product.imagem_fonte = "Indiana"
    source_product.imagem_sku_origem = "IND123"
    source_product.imagem_ean = "7891234567895"
    source_product.imagem_match = "ean"
    source_product.imagem_status = "verificada"
    source_product.imagem_verificada_em = datetime.now(UTC)
    source_product.imagem_atualizada_em = datetime.now(UTC)
    source.add(source_product)
    source.flush()
    source.add(_offer(source_product, source_pharmacy))
    source.commit()
    exported = export_image_references(source)
    assert exported["schema_version"] == 1
    assert "preco" not in str(exported["records"]).lower()
    assert "password" not in str(exported["records"]).lower()

    destination = _database()
    destination_pharmacy = _farmacia(destination)
    decoy = _product("Outro registro sem vínculo")
    target = _product("Produto com EAN", "7891234567895")
    destination.add_all([decoy, target])
    destination.flush()
    destination.add(_offer(target, destination_pharmacy))
    destination.commit()
    assert target.id != source_product.id

    result = import_image_references(destination, exported)
    assert result["associated"] == 1
    assert result["conflict_count"] == 0
    assert result["unmatched_count"] == 0
    assert target.imagem_url == IMAGE_URL
    assert target.imagem_status == "pendente"
    assert target.imagem_verificada_em is None

    repeated = import_image_references(destination, exported)
    assert repeated["associated"] == 0
    assert repeated["already_present"] == 1
    source.close()
    destination.close()


def test_import_reports_conflicting_identity_and_does_not_overwrite() -> None:
    db = _database()
    pharmacy = _farmacia(db)
    by_ean = _product("EAN destino", "7891234567895")
    by_sku = _product("SKU destino")
    by_sku.imagem_url = "https://farmaciaindiana.vteximg.com.br/arquivos/existing.jpg"
    db.add_all([by_ean, by_sku])
    db.flush()
    offer = _offer(by_sku, pharmacy)
    db.add(offer)
    db.commit()

    document = {
        "schema": "preco-bao.image-references",
        "schema_version": 1,
        "records": [
            {
                "source_catalog_id": 999,
                "identity": {
                    "ean": "7891234567895",
                    "offers": [
                        {
                            "pharmacy": "Indiana",
                            "sku": "IND123",
                            "product_url": PRODUCT_URL,
                        }
                    ],
                },
                "image": {"url": IMAGE_URL, "source": "Indiana"},
            }
        ],
    }
    result = import_image_references(db, document)
    assert result["associated"] == 0
    assert result["conflict_count"] == 1
    assert by_ean.imagem_url is None
    assert by_sku.imagem_url.endswith("existing.jpg")
    db.close()


def test_import_records_missing_and_unsafe_references() -> None:
    db = _database()
    document = {
        "schema": "preco-bao.image-references",
        "schema_version": 1,
        "records": [
            {"source_catalog_id": 1, "identity": {}, "image": {"url": IMAGE_URL}},
            {
                "source_catalog_id": 2,
                "identity": {"ean": "1234567890123"},
                "image": {"url": "http://127.0.0.1/private.jpg"},
            },
        ],
    }
    result = import_image_references(db, document)
    assert result["unmatched_count"] == 1
    assert result["invalid_count"] == 1
    db.close()


def test_import_restores_legacy_duplicate_name_group_by_shared_official_sku() -> None:
    db = _database()
    db.add_all(
        [_product("Legacy identical product"), _product("Legacy identical product")]
    )
    db.commit()
    document = {
        "schema": "preco-bao.image-references",
        "schema_version": 1,
        "records": [
            {
                "source_catalog_id": source_id,
                "identity": {
                    "ean": None,
                    "name": "Legacy identical product",
                    "offers": [],
                },
                "image": {
                    "url": IMAGE_URL,
                    "source": "Indiana",
                    "sku": "IND123",
                    "match": "catalog_duplicate",
                },
            }
            for source_id in (501, 502)
        ],
    }
    result = import_image_references(db, document)
    assert result["associated"] == 2
    assert result["unmatched_count"] == 0
    assert result["conflict_count"] == 0
    assert all(
        product.imagem_url == IMAGE_URL for product in db.query(CatalogoBase).all()
    )

    repeated = import_image_references(db, document)
    assert repeated["associated"] == 0
    assert repeated["already_present"] == 2
    db.close()


def test_import_leaves_duplicate_name_group_unmatched_when_source_skus_disagree() -> (
    None
):
    db = _database()
    db.add_all([_product("Ambiguous duplicate"), _product("Ambiguous duplicate")])
    db.commit()
    document = {
        "schema": "preco-bao.image-references",
        "schema_version": 1,
        "records": [
            {
                "source_catalog_id": source_id,
                "identity": {"ean": None, "name": "Ambiguous duplicate", "offers": []},
                "image": {
                    "url": IMAGE_URL,
                    "source": "Indiana",
                    "sku": sku,
                    "match": "sku",
                },
            }
            for source_id, sku in ((601, "IND123"), (602, "IND456"))
        ],
    }
    result = import_image_references(db, document)
    assert result["associated"] == 0
    assert result["unmatched_count"] == 2
    assert all(product.imagem_url is None for product in db.query(CatalogoBase).all())
    db.close()


def test_external_generic_reference_requires_confirmed_exact_ean_and_domain() -> None:
    url = "https://www.farmaciasnissei.com.br/media/medicamentos/caixa.webp"
    valid, match, reason = validate_image_association(
        image_url=url,
        pharmacy_name="Nissei",
        sku=None,
        ean="7898581711254",
        product_url="https://www.farmaciasnissei.com.br/neuleptil/p",
        identity_confirmed=True,
    )
    assert valid
    assert match == "ean"
    assert reason is None

    valid, _, reason = validate_image_association(
        image_url=url,
        pharmacy_name="Nissei",
        sku=None,
        ean="7898581711254",
        product_url="https://other.example/neuleptil/p",
        identity_confirmed=True,
    )
    assert not valid
    assert reason
