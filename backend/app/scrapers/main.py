"""
services/scraper_service.py
---------------------------
Serviço de extração massiva. Itera por todas as páginas do catálogo
utilizando a técnica de mineração do objeto __STATE__.
"""

import asyncio
import httpx
import json
from urllib.parse import urljoin
from typing import List, Dict, Any
# Supondo que você criou estes arquivos:
# from utils.validators import validar_ean13 

async def extrair_todos_produtos():
    """
    Percorre todo o catálogo da Farmácia Indiana.
    """
    url_base = "https://www.farmaciaindiana.com.br"
    # A rota /busca vazia costuma listar todos os produtos por ordem de relevância/id
    url_atual = f"{url_base}/busca" 
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        pagina = 1
        while url_atual:
            try:
                print(f"Processando página {pagina}...")
                response = await client.get(url_atual)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Mineração do __STATE__ (Idem ao código anterior)
                template_tag = soup.find('template', {'data-varname': '__STATE__'})
                if template_tag:
                    script_tag = template_tag.find('script')
                    estado_json = json.loads(script_tag.string)
                    
                    produtos_da_pagina = processar_estado_vtex(estado_json, url_base)
                    
                    # Aqui você enviaria para o seu Service de Banco de Dados
                    # await salvar_no_banco(produtos_da_pagina)
                    print(f"Coletados {len(produtos_da_pagina)} produtos na página {pagina}.")

                # Logica de Próxima Página
                botao_next = soup.find('a', rel='next')
                if botao_next:
                    url_atual = urljoin(url_base, botao_next.get('href'))
                    pagina += 1
                    # Aumentar o delay em scraping massivo é vital para evitar BAN
                    await asyncio.sleep(2.5) 
                else:
                    url_atual = None
                    print("Varredura completa concluída.")

            except Exception as e:
                print(f"Erro na página {pagina}: {e}")
                # Estratégia de Retry ou Log de Erro
                break

def processar_estado_vtex(estado_json: Dict, url_base: str) -> List[Dict]:
    """Extrai e limpa os dados do dicionário de estado."""
    resultados = []
    for chave, dados in estado_json.items():
        if chave.startswith("Product:sp-") and "." not in chave:
            p_id = dados.get("productId")
            base_key = f"Product:sp-{p_id}.items({{\"filter\":\"FIRST_AVAILABLE\"}}).0"
            
            sku_data = estado_json.get(base_key, {})
            offer_key = f"${base_key}.sellers.0.commertialOffer"
            offer_data = estado_json.get(offer_key, {})
            
            ean = sku_data.get("ean")
            
            # Validação na entrada
            # if not validar_ean13(ean): continue

            resultados.append({
                "ean": ean,
                "nome": dados.get("productName"),
                "preco": offer_data.get("Price", 0.0),
                "link": urljoin(url_base, dados.get("link", ""))
            })
    return resultados