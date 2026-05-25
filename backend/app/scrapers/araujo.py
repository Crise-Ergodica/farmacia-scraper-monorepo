"""
Scraper especializado para extração de dados da Drogaria Araujo via HTML parsing.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Literal
from bs4 import BeautifulSoup, Tag
from curl_cffi import requests
from app.scrapers.base import BasePharmacyScraper

class AraujoScraper(BasePharmacyScraper):
    def __init__(self, num_workers: int = 3, batch_size: int = 50):
        super().__init__(
            farmacia_cnpj="17256512000116",
            farmacia_razao_social="Drogaria Araujo S.A",
            farmacia_nome_fantasia="Araujo",
            farmacia_endereco="Extração via HTML Scraper",
            num_workers=num_workers,
            batch_size=batch_size
        )
        self.url_base = "https://www.araujo.com.br/medicamentos?page={}"

    async def extrair_catalogo(self) -> None:
        """
        Método principal do scraper da Araujo.
        Varre as páginas e envia os produtos limpos para a fila base.
        """
        pagina = 1
        processando = True

        # Usando AsyncSession do curl_cffi para imitar o comportamento de browser
        # Injetando headers para contornar o bloqueio de bot (Cloudflare/Akamai) que retorna 0 produtos
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.araujo.com.br/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        async with requests.AsyncSession(impersonate="chrome110", verify=False, headers=headers) as session:
            while processando:
                print(f"Buscando Drogaria Araujo - Página {pagina}...")
                
                try:
                    url = self.url_base.format(pagina)
                    # Envolvemos a requisição no mecanismo de backoff
                    async def fetch():
                        return await session.get(url, timeout=30.0)

                    response = await self.executar_com_backoff(fetch)

                    if response.status_code == 404:
                        print("Fim do catálogo (404).")
                        break

                    html_content = response.text
                    print(f"DEBUG: Tamanho do HTML recebido: {len(html_content)} bytes")

                    # Se não encontrar o wrapper principal de produtos, provável fim
                    if "productTile" not in html_content:
                        print(f"Página {pagina} sem produtos. Varredura finalizada.")
                        break

                    produtos_limpos = self.adaptar_parser_araujo_html(html_content)

                    if not produtos_limpos:
                        print(f"Nenhum produto extraído na página {pagina}. Varredura finalizada.")
                        break

                    # Envia os produtos para a fila assíncrona
                    for prod in produtos_limpos:
                        await self.fila.put(prod)
                    
                    print(f"✓ {len(produtos_limpos)} medicamentos enfileirados da página {pagina}.")

                    pagina += 1

                    # CONDICIONADO PARA O TESTE: Parar após a página 2
                    if pagina > 2:
                        print("Limite de teste atingido. Encerrando extração da Araujo.")
                        break

                except Exception as e:
                    print(f"Falha inesperada no scraper da Araujo: {e}")
                    break

    def adaptar_parser_araujo_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Analisa o DOM do HTML da Araujo utilizando BeautifulSoup para extrair os produtos.
        Aproveita os metadados JSON do Google Tag Manager embutidos no HTML e
        extrai o EAN através de Regex na URL da imagem.
        """
        catalogo_limpo = []
        soup = BeautifulSoup(markup=html_content, features="html.parser")
        # DEBUG: Liste as classes de todas as divs para ver se o nome mudou
        divs = soup.find_all("div")
        classes_encontradas = set()
        for div in divs:
            if div.get("class"):
                classes_encontradas.update(div.get("class"))

        print(f"DEBUG: Classes CSS encontradas na página: {list(classes_encontradas)[:20]}...")
        # Verifica se o seletor antigo ainda existe
        tem_product_tile = soup.find_all(class_="productTile")
        print(f"DEBUG: Quantidade de elementos 'productTile' encontrados: {len(tem_product_tile)}")

        cards_produtos = soup.find_all(name="div", class_="productTile")

        for card in cards_produtos:
            try:
                # 1. Link do produto
                link_path = card.get(key="data-url")
                if isinstance(link_path, list):
                    link_path = str(link_path[0])
                elif link_path:
                    link_path = str(link_path)
                else:
                    link_path = ""

                link = f"https://www.araujo.com.br{link_path}" if link_path else ""

                # 2. Dados GTM
                gtm_tag = card.find("div", class_="gtmContainer__productTile")
                gtm_data_str = gtm_tag.get("data-gtmga4data") if gtm_tag else "{}"
                
                if isinstance(gtm_data_str, list):
                    gtm_data_str = str(gtm_data_str[0])
                elif gtm_data_str:
                    gtm_data_str = str(gtm_data_str)

                gtm_data = json.loads(gtm_data_str) if gtm_data_str else {}
                
                # 3. Nome e Preço
                nome = gtm_data.get("item_name", "")
                if not nome:
                    tag_nome = card.find("a", class_="productTile__name")
                    nome = tag_nome.text.strip() if tag_nome else "Nome não encontrado"

                preco = gtm_data.get("price", 0.0)
                if not preco:
                    tag_preco = card.find("span", class_="productPrice__price")
                    if tag_preco:
                        texto_preco = tag_preco.text.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        preco = float(texto_preco)

                # 4. Imagem e EAN
                tag_img = card.find(name="img", class_="productTile__imageWrapper__img")
                imagem_url = tag_img.get(key="data-src") or tag_img.get(key="src") if tag_img else ""
                
                if isinstance(imagem_url, list):
                    imagem_url = str(imagem_url[0])
                elif imagem_url:
                    imagem_url = str(imagem_url)
                else:
                    imagem_url = ""

                if imagem_url and imagem_url.startswith("/"):
                    imagem_url = f"https://www.araujo.com.br{imagem_url}"

                ean = ""
                if imagem_url:
                    match = re.search(pattern=r'(\d{13,14})', string=imagem_url)
                    if match:
                        ean = match.group(1).strip().replace("-", "")

                # 5. ID Interno
                id_interno = card.get(key="data-pid", default="")
                if isinstance(id_interno, list):
                    id_interno = str(id_interno[0])
                elif id_interno:
                    id_interno = str(id_interno)

                if link:
                    catalogo_limpo.append({
                        "id": id_interno,
                        "sku_interno": f"ARJ{id_interno}",
                        "ean": ean,
                        "name_search": nome,
                        "preco": float(preco),
                        "link": link,
                        "imagem_url": imagem_url
                    })
            except Exception as e:
                print(f"Erro ao parsear um card específico: {e}")
                continue
            
        return catalogo_limpo


if __name__ == "__main__":
    print("Iniciando varredura na Drogaria Araujo via HTML com Nova Arquitetura...")
    scraper = AraujoScraper(num_workers=3, batch_size=50)
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\nInterrompido pela usuária.")
