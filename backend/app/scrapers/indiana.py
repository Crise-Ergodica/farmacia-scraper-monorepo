"""
app.scrapers.indiana
====================

Este módulo fornece utilitários para a extração (scraping) do catálogo de
medicamentos da Farmácia Indiana consumindo diretamente sua API REST.

A utilidade principal deste módulo é automatizar a varredura de produtos da loja,
lidando com a paginação da API, extraindo campos de interesse (como EAN, nome, 
preço e imagens) e despachando os dados limpos para a camada de persistência 
(banco de dados) de forma assíncrona para não bloquear o loop de eventos.
"""

import asyncio
from typing import Any, Dict, List

import httpx

async def extrair_todos_produtos() -> None:
    """
    Extrai todos os medicamentos iterando sobre a paginação da API REST.

    A função faz requisições assíncronas para a API da Farmácia Indiana,
    controlando o ``offset`` e a página atual. Quando obtém sucesso, repassa
    os dados brutos para a função :func:`adaptar_parser_rest` e despacha os
    dados limpos para o banco de dados através de uma thread separada,
    evitando bloqueios de I/O.

    O loop é interrompido automaticamente caso a API retorne status 404 ou 
    uma lista vazia de produtos.

    :raises httpx.HTTPStatusError: Se a API retornar erros da família 4xx 
        (exceto o 404 de fim de catálogo tratado) ou 5xx.
    :raises Exception: Para qualquer falha genérica ou de conexão inesperada.
    
    :returns: None
    :rtype: None
    """
    url_base_api = "https://www.farmaciaindiana.com.br/api/catalog_system/pub/products/search/medicamentos"
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    itens_por_pagina = 49  
    offset = 0
    pagina = 1
    processando = True

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        while processando:
            print(f"Buscando Página {pagina} (Itens {offset} a {offset + itens_por_pagina})...")
            
            try:
                url_paginada = f"{url_base_api}?_from={offset}&_to={offset + itens_por_pagina}"
                resp = await client.get(url_paginada)
                
                # Tratamento de fim de catálogo explícito
                if resp.status_code == 404:
                    print("Fim do catálogo (404).")
                    break

                # Levanta erro apenas para 4xx e 5xx (200 e 206 passam direto)
                resp.raise_for_status()
                
                produtos_brutos = resp.json()

                if not produtos_brutos:
                    print("Lista vazia. Varredura finalizada.")
                    break

                produtos_limpos = adaptar_parser_rest(produtos_brutos)
                
                # Despacha para thread de I/O
                await asyncio.to_thread(salvar_no_banco, produtos_limpos)
                
                print(f"✓ {len(produtos_limpos)} medicamentos processados.")
                
                pagina += 1
                offset += (itens_por_pagina + 1)
                await asyncio.sleep(2.0)

            except httpx.HTTPStatusError as e:
                print(f"Erro HTTP na página {pagina}: {e.response.status_code}")
                break
            except Exception as e:
                print(f"Falha inesperada: {e}")
                break


def adaptar_parser_rest(produtos_brutos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analisa e limpa a resposta bruta de produtos em JSON.

    Recebe a lista de dicionários brutos da API VTEX/REST da loja e filtra
    apenas as informações essenciais para o sistema, garantindo também 
    fallbacks, como a busca de código EAN em referências secundárias.

    :param produtos_brutos: Lista de dicionários representando o JSON original 
        de produtos retornados pela API.
    :type produtos_brutos: List[Dict[str, Any]]
    
    :returns: Lista de dicionários contendo os dados padronizados de cada 
        produto (id, ean, nome, preco, link, imagem_url).
    :rtype: List[Dict[str, Any]]
    """
    catalogo_limpo = []
    
    for prod in produtos_brutos:
        itens = prod.get("items", [])
        if not itens:
            continue
            
        item_principal = itens[0]
        
        # Correção: Fallback do EAN inserido
        ean = item_principal.get("ean")
        if not ean:
            refs = item_principal.get("referenceId", [])
            ean = refs[0].get("Value") if refs else ""
            
        vendedores = item_principal.get("sellers", [])
        preco = 0.0
        if vendedores:
            preco = vendedores[0].get("commertialOffer", {}).get("Price", 0.0)
            
        imagens = item_principal.get("images", [])
        imagem_url = imagens[0].get("imageUrl") if imagens else None

        catalogo_limpo.append({
            "id": item_principal.get("itemId"),
            "ean": ean,
            "nome": prod.get("productName"),
            "preco": preco,
            "link": prod.get("link"),
            "imagem_url": imagem_url
        })
        
    return catalogo_limpo


if __name__ == "__main__":
    print("Iniciando varredura via API REST...")
    try:
        asyncio.run(extrair_todos_produtos())
    except KeyboardInterrupt:
        print("\nInterrompido pela usuária.")
        

# def salvar_no_banco(produtos: List[Dict[str, Any]]) -> None:
#     """
#     Persiste uma lista de produtos no banco de dados.
#     Atualiza o preço caso o medicamento (EAN) já exista.
#     """
#     db = SessionLocal()
    
#     try:
#         cnpj_padrao = "00000000000100"
#         farmacia = db.query(Farmacia).filter(Farmacia.cnpj == cnpj_padrao).first()

#         if not farmacia:
#             farmacia = Farmacia(
#                 cnpj=cnpj_padrao,
#                 razao_social="Farmácia Indiana - Web Scraper",
#                 nome_fantasia="Indiana",
#                 endereco_completo="Extração API REST"
#             )
#             db.add(farmacia)
#             db.commit()
#             db.refresh(farmacia)

#         for prod in produtos:
#             ean = prod.get('ean')

#             if not ean or not validar_ean13(ean):
#                 continue

#             medicamento_existente = db.query(Medicamento).filter(Medicamento.codigo_barras == ean).first()

#             if not medicamento_existente:
#                 novo_med = Medicamento(
#                     codigo_barras=ean,
#                     nome=prod['nome'],
#                     preco=prod['preco'],
#                     url_origem=prod['link'],
#                     principio_ativo="Não informado",
#                     laboratorio="Não informado",
#                     farmacia_id=farmacia.id
#                 )
#                 db.add(novo_med)
#             else:
#                 medicamento_existente.preco = prod['preco']
#                 medicamento_existente.url_origem = prod['link']

#         db.commit()

#     except SQLAlchemyError as e:
#         db.rollback()
#         print(f"[ERRO DB] Falha na persistência: {e}")
#     finally:
#         db.close()