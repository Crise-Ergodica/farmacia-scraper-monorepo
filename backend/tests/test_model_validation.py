import pytest
from pydantic import ValidationError
from app.schemas.oferta import ProdutoExtraidoSchema
from app.schemas.catalogo import CatalogoBaseSchema

def test_produto_extraido_schema_validacao_sucesso():
    dados = {
        "id": "12345",
        "sku_interno": "ARJ12345",
        "ean": "1234567890123",
        "name_search": "Dipirona 500mg",
        "preco": 10.50,
        "link": "https://farmacia.com/dipirona",
        "imagem_url": "https://farmacia.com/img.jpg"
    }

    produto = ProdutoExtraidoSchema.model_validate(dados)
    assert produto.ean == "1234567890123"
    assert produto.sku_interno == "ARJ12345"
    assert produto.name_search == "Dipirona 500mg"
    assert produto.preco == 10.50

def test_produto_extraido_schema_ean_muito_longo():
    dados = {
        "id": "12345",
        "sku_interno": "ARJ12345",
        "ean": "123456789012345", # 15 dígitos
        "name_search": "Dipirona 500mg",
        "preco": 10.50,
        "link": "https://farmacia.com/dipirona"
    }

    with pytest.raises(ValidationError) as exc_info:
        ProdutoExtraidoSchema.model_validate(dados)

    assert "String should have at most 14 characters" in str(exc_info.value)

def test_produto_extraido_schema_limpeza_ean():
    dados = {
        "id": "12345",
        "sku_interno": "ARJ12345",
        "ean": " 123-456 789 ",
        "name_search": "Dipirona 500mg",
        "preco": 10.50,
        "link": "https://farmacia.com/dipirona"
    }

    produto = ProdutoExtraidoSchema.model_validate(dados)
    assert produto.ean == "123456789"

def test_catalogo_base_schema_validacao_sucesso():
    dados = {
        "codigo_barras": "1234567890123",
        "name_search": "Dipirona 500mg",
        "principio_ativo": "Dipirona Monoidratada",
        "laboratorio": "Medley",
        "exige_receita": False,
        "categorias": ["Genérico", "Analgésico"]
    }

    catalogo = CatalogoBaseSchema.model_validate(dados)
    assert catalogo.codigo_barras == "1234567890123"
    assert catalogo.name_search == "Dipirona 500mg"