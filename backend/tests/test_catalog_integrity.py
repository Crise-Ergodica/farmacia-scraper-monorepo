"""Identity evidence must be exact before catalog GTINs are written."""

from scripts.auditar_integridade_catalogo import product_data, valid_gtin


def test_official_product_data_requires_product_json_ld():
    page = (
        '<script type="application/ld+json">'
        '{"@type":"Product","name":"Glyxambi 25mg + 5mg com 30 Comprimidos",'
        '"sku":"7290","gtin13":"7896026306751"}'
        "</script>"
    )
    assert product_data(page) == {
        "@type": "Product",
        "name": "Glyxambi 25mg + 5mg com 30 Comprimidos",
        "sku": "7290",
        "gtin13": "7896026306751",
    }
    assert product_data('<script type="application/ld+json">{}</script>') is None


def test_gtin_checksum_rejects_typo():
    assert valid_gtin("7896026306751")
    assert not valid_gtin("7896026306752")
    assert not valid_gtin("789602630675")
