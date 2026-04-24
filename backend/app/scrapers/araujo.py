#TODO: Criando o 2° Scrapper: Farmacia Araujo!

# """
# app.scrapers.araujo
# ===================

# Este módulo fornece utilitários para a extração (scraping) do catálogo de
# medicamentos da Drogaria Araujo.

# Implementa rotinas assíncronas para consumo de dados, tratamento de paginação,
# resiliência de rede (Jitter e Backoff) e persistência em lote utilizando
# os modelos do SQLAlchemy.
# """

# import asyncio
# import random
# from typing import Any, Dict, List
# import httpx

# from app.core.database import SessionLocal
# from app.core.utils import validar_ean13
# from app.models.farmacia import Farmacia
# from app.models.catalogo import CatalogoBase
# from app.models.oferta_farmacia import OfertaFarmacia
# from sqlalchemy.exc import SQLAlchemyError


# async def extrair_todos_produtos() -> None:
#     """
#     Controla o loop principal de varredura do catálogo da Araujo.
#     """
#     # URL temporária: precisaremos mapear a rota real da Araujo
#     url_base_api = "https://www.araujo.com.br/api/catalog_system/pub/products/search/medicamentos"
    
#     headers = {
#         "Accept": "application/json",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#     }

#     itens_por_pagina = 49  
#     offset = 0
#     pagina = 1
#     processando = True

#     async with httpx.AsyncClient(headers=headers, timeout=30.0, verify=False) as client:
#         while processando:
#             print(f"Buscando Araujo: Página {pagina} (Itens {offset} a {offset + itens_por_pagina})...")
            
#             try:
#                 url_paginada = f"{url_base_api}?_from={offset}&_to={offset + itens_por_pagina}"
#                 resp = await client.get(url_paginada)
                
#                 if resp.status_code == 404:
#                     print("Fim do catálogo (404).")
#                     break

#                 resp.raise_for_status()
#                 produtos_brutos = resp.json()

#                 if not produtos_brutos:
#                     print("Lista vazia. Varredura finalizada.")
#                     break

#                 produtos_limpos = adaptar_parser_araujo(produtos_brutos)
#                 await asyncio.to_thread(salvar_no_banco, produtos_limpos)
#                 print(f"[{pagina}] {len(produtos_limpos)} medicamentos da Araujo processados.")
                
#                 pagina += 1
#                 offset += (itens_por_pagina + 1)
                
#                 # Jitter implementado para mitigar bloqueios
#                 tempo_pausa = random.uniform(2.0, 4.0)
#                 await asyncio.sleep(tempo_pausa)

#             except httpx.HTTPStatusError as e:
#                 status = e.response.status_code
                
#                 if status == 429:
#                     print(f"Rate limit (429) na Araujo. Pausando por 60 segundos...")
#                     await asyncio.sleep(60.0)
#                     continue 
                
#                 elif status >= 500:
#                     print(f"Erro {status} no servidor Araujo. Aguardando 10s...")
#                     await asyncio.sleep(10.0)
#                     continue 
                    
#                 else:
#                     print(f"Erro HTTP bloqueante na página {pagina}: {status}")
#                     break
                    
#             except Exception as e:
#                 print(f"Falha inesperada: {e}")
#                 break


# def adaptar_parser_araujo(produtos_brutos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Analisa e limpa a resposta bruta de produtos da Araujo.
#     """
#     catalogo_limpo = []
    
#     for prod in produtos_brutos:
#         # A lógica exata de extração dependerá do payload da Araujo
#         # Este é um esqueleto baseado na estrutura VTEX padrão
#         itens = prod.get("items", [])
#         if not itens:
#             continue
            
#         item_principal = itens[0]
        
#         ean = item_principal.get("ean")
#         if not ean:
#             refs = item_principal.get("referenceId", [])
#             ean = refs[0].get("Value") if refs else ""
            
#         vendedores = item_principal.get("sellers", [])
#         preco = 0.0
#         if vendedores:
#             preco = vendedores[0].get("commertialOffer", {}).get("Price", 0.0)
            
#         imagens = item_principal.get("images", [])
#         imagem_url = imagens[0].get("imageUrl") if imagens else None

#         catalogo_limpo.append({
#             "id": item_principal.get("itemId"),
#             "ean": ean,
#             "nome": prod.get("productName"),
#             "preco": preco,
#             "link": prod.get("link"),
#             "imagem_url": imagem_url
#         })
        
#     return catalogo_limpo
        

# def salvar_no_banco(produtos: List[Dict[str, Any]]) -> None:
#     """
#     Persiste uma lista de produtos no banco de dados.
#     """
#     db = SessionLocal()
    
#     try:
#         # CNPJ Matriz da Araujo
#         cnpj_padrao = "17256512000116" 
#         farmacia = db.query(Farmacia).filter(Farmacia.cnpj == cnpj_padrao).first()

#         if not farmacia:
#             farmacia = Farmacia(
#                 cnpj=cnpj_padrao,
#                 razao_social="Drogaria Araujo S.A",
#                 nome_fantasia="Araujo",
#                 endereco_completo="Extração API REST"
#             )
#             db.add(farmacia)
#             db.commit()
#             db.refresh(farmacia)

#         for prod in produtos:
#             ean = prod.get('ean')

#             if not ean or not validar_ean13(ean):
#                 continue

#             catalogo_item = db.query(CatalogoBase).filter(CatalogoBase.codigo_barras == ean).first()

#             if not catalogo_item:
#                 catalogo_item = CatalogoBase(
#                     codigo_barras=ean,
#                     nome=prod['nome'],
#                     principio_ativo="Não informado",
#                     laboratorio="Não informado",
#                     exige_receita=False
#                 )
#                 db.add(catalogo_item)
#                 db.commit()
#                 db.refresh(catalogo_item)

#             oferta_existente = db.query(OfertaFarmacia).filter(
#                 OfertaFarmacia.url_origem == prod['link']
#             ).first()

#             if not oferta_existente:
#                 oferta_existente = db.query(OfertaFarmacia).filter(
#                     OfertaFarmacia.catalogo_id == catalogo_item.id,
#                     OfertaFarmacia.farmacia_id == farmacia.id
#                 ).first()

#             if not oferta_existente:
#                 nova_oferta = OfertaFarmacia(
#                     preco=prod['preco'],
#                     quantidade_estoque=1,
#                     disponivel=True,
#                     url_origem=prod['link'],
#                     imagem_url=prod.get('imagem_url'),
#                     farmacia_id=farmacia.id,
#                     catalogo_id=catalogo_item.id
#                 )
#                 db.add(nova_oferta)
#             else:
#                 oferta_existente.preco = prod['preco']
                
#                 if oferta_existente.url_origem != prod['link']:
#                     oferta_existente.url_origem = prod['link']
                    
#                 if prod.get('imagem_url'):
#                     oferta_existente.imagem_url = prod['imagem_url']
            
#         db.commit()

#     except SQLAlchemyError as e:
#         db.rollback()
#         print(f"[ERRO DB] Falha na persistência: {e}")
#     finally:
#         db.close()


# if __name__ == "__main__":
#     print("Iniciando varredura na Drogaria Araujo...")
#     try:
#         asyncio.run(extrair_todos_produtos())
#     except KeyboardInterrupt:
#         print("\nInterrompido pela usuária.")