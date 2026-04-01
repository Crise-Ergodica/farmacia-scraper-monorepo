"""
core.utils
----------
Módulo de utilitários transversais e funções auxiliares do sistema.

Este módulo centraliza algoritmos independentes, ferramentas de validação
matemática e rotinas de higienização de dados que suportam toda a infraestrutura
do web scraper.
"""

import json
from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError 

def validar_ean13(ean: str) -> bool:
    """
    Valida a integridade de um código de barras EAN-13 através do cálculo do seu dígito verificador.
    """
    if not (isinstance(ean, str) and len(ean) == 13 and ean.isdigit()):
        return False
    
    try:
        corpo = [int(d) for d in ean[:12]]
        pesos = [1, 3] * 6
        soma = sum(d * p for d, p in zip(corpo, pesos))
        digito_esperado = (10 - (soma % 10)) % 10
        return int(ean[12]) == digito_esperado
    except ValueError:
        return False


def parse_vtex_graphql_response(json_payload):
    """
    Extrai informações estruturadas de produtos de uma resposta GraphQL da VTEX.
    """
    produtos_brutos = json_payload.get("data", {}).get("productSearch", {}).get("products", [])
    catalogo_limpo = []

    for produto in produtos_brutos:
        itens = produto.get("items", [])
        if not itens:
            continue
            
        item_principal = itens[0]
        item_id = item_principal.get("itemId")
        nome = item_principal.get("name")
        link_relativo = produto.get("link")
        link_completo = f"https://www.farmaciaindiana.com.br{link_relativo}" if link_relativo else None
        
        imagens = item_principal.get("images", [])
        imagem_url = imagens[0].get("imageUrl") if imagens else None
        
        ean = item_principal.get("ean")
        if not ean:
            refs = item_principal.get("referenceId", [])
            ean = refs[0].get("Value") if refs else ""
        
        vendedores = item_principal.get("sellers", [])
        preco = None
        if vendedores:
            oferta = vendedores[0].get("commertialOffer", {})
            preco = oferta.get("Price")

        catalogo_limpo.append({
            "id": item_id,
            "ean": ean, 
            "nome": nome,
            "preco": preco,
            "link": link_completo,
            "imagem_url": imagem_url
        })

    return catalogo_limpo