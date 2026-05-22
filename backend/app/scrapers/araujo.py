"""
app.scrapers.araujo
===================
"""

# 1. Bibliotecas Padrão do Python
import asyncio
import json
import random
import re
from typing import Any, Dict, List, Literal

# 2. Bibliotecas de Terceiros
from bs4.element import AttributeValueList
from curl_cffi import requests 
from bs4 import BeautifulSoup, Tag
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

# 3. Módulos Locais da Aplicação
from app.core.database import SessionLocal
from app.core.utils import validar_ean13
from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.models.oferta_farmacia import OfertaFarmacia
from app.schemas.oferta import ProdutoExtraidoSchema
from pydantic import ValidationError
from app.services.enriquecimento import ServicoEnriquecimentoFarmacologico


async def extrair_todos_produtos() -> None:
    """
    Controla o loop principal de varredura do catálogo da Araujo via HTML.
    """
    url_base = "https://www.araujo.com.br/medicamentos"
    
    # O curl_cffi já envia a maioria dos headers corretos de navegador, 
    # mas mantemos o Accept-Language por garantia.
    headers = {
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    pagina = 1
    processando = True

    # TROCAMOS AQUI: Usando AsyncSession com impersonate="chrome"
    async with requests.AsyncSession(impersonate="chrome", headers=headers, timeout=30.0) as client:
        while processando:
            print(f"Buscando Araujo: Página {pagina}...")
            
            try:
                url_paginada = f"{url_base}?page={pagina}" if pagina > 1 else url_base
                resp = await client.get(url=url_paginada)
                
                if resp.status_code == 404:
                    print("Fim do catálogo (404).")
                    break

                resp.raise_for_status()
                html_content = resp.text

                # Passamos o HTML cru para o parser
                produtos_limpos = adaptar_parser_araujo_html(html_content=html_content)

                if not produtos_limpos:
                    print("Nenhum produto encontrado nesta página. Varredura finalizada.")
                    break

                await asyncio.to_thread(salvar_no_banco, produtos_limpos)
                print(f"[{pagina}] {len(produtos_limpos)} medicamentos da Araujo processados.")
                
                pagina += 1
                
                # ADICIONADO PARA O TESTE: Parar após a página 2
                if pagina > 2:
                    print("Limite de teste atingido. Encerrando.")
                    break
                
                tempo_pausa = random.uniform(2.0, 5.0)
                await asyncio.sleep(tempo_pausa)

            except requests.errors.RequestsError as e: 
                print(f"Erro de conexão na Araujo: {e}")
                break
                
            except Exception as e:
                # Acessa o atributo de forma dinâmica e segura para tipagem estática
                response: Any | None = getattr(e, "response", None)
                
                if response is not None:
                    status: int = getattr(response, "status_code", 0)
                    
                    if status == 429:
                        print(f"Rate limit (429) na Araujo. Pausando por 60 segundos...")
                        await asyncio.sleep(60.0)
                        continue 
                    elif status >= 500:
                        print(f"Erro {status} no servidor Araujo. Aguardando 10s...")
                        await asyncio.sleep(10.0)
                        continue 
                    else:
                        print(f"Erro HTTP bloqueante na página {pagina}: {status}")
                        break
                else:
                    print(f"Falha inesperada: {e}")
                    break

def adaptar_parser_araujo_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Analisa o DOM do HTML da Araujo utilizando BeautifulSoup para extrair os produtos.
    Aproveita os metadados JSON do Google Tag Manager embutidos no HTML e 
    extrai o EAN através de Regex na URL da imagem.
    """
    catalogo_limpo = []
    soup = BeautifulSoup(markup=html_content, features="html.parser")
    
    # Busca a classe principal do card do produto
    cards_produtos = soup.find_all(name="div", class_="productTile")
    
    for card in cards_produtos:
        try:
            # 1. Link do produto (Pegando diretamente do atributo do card)
            link_path: str | AttributeValueList | None = card.get(key="data-url")
            # Validação para evitar falhas de tipagem
            if isinstance(link_path, list):
                link_path = str(link_path[0])
            elif link_path:
                link_path = str(link_path)
            else:
                link_path = ""
                
            link = f"https://www.araujo.com.br{link_path}" if link_path else ""

            # 2. Dados GTM (Google Tag Manager)
            # A Araujo injeta um JSON limpo com nome e preço aqui, o que evita erros de formatação
            gtm_tag: Tag | None = card.find("div", class_="gtmContainer__productTile")
            gtm_data_str: str | AttributeValueList | None = gtm_tag.get("data-gtmga4data") if gtm_tag else "{}"
            
            # Garantir que a string GTM é tratada corretamente
            if isinstance(gtm_data_str, list):
                gtm_data_str = str(gtm_data_str[0])
            elif gtm_data_str:
                gtm_data_str = str(gtm_data_str)
                
            gtm_data = json.loads(gtm_data_str) if gtm_data_str else {}
            
            # 3. Nome e Preço
            nome = gtm_data.get("item_name", "")
            if not nome:
                tag_nome: Tag | None = card.find("a", class_="productTile__name")
                nome: Any | Literal['Nome não encontrado'] = tag_nome.text.strip() if tag_nome else "Nome não encontrado"
                
            preco = gtm_data.get("price", 0.0)
            if not preco:
                tag_preco: Tag | None = card.find("span", class_="productPrice__price")
                if tag_preco:
                    texto_preco = tag_preco.text.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    preco = float(texto_preco)

            # 4. Imagem e EAN
            tag_img: Tag | None = card.find(name="img", class_="productTile__imageWrapper__img")
            
            # Algumas imagens usam lazy loading via data-src
            imagem_url: str | AttributeValueList | None = tag_img.get(key="data-src") or tag_img.get(key="src") if tag_img else ""
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
                # Procura por 13 ou 14 números seguidos na string da URL da imagem
                match: re.Match[str] | None = re.search(pattern=r'(\d{13,14})', string=imagem_url)
                if match:
                    ean: str | Any = match.group(1)

            # 5. ID Interno (Fallback caso o EAN falhe)
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
        

def salvar_no_banco(produtos: List[Dict[str, Any]]) -> None:
    """
    Persiste uma lista de produtos no banco de dados.
    Esta função permanece praticamente idêntica à do scraper da Indiana.
    """
    db: Session = SessionLocal()
    
    try:
        # CNPJ Matriz da Araujo
        cnpj_padrao = "17256512000116" 
        farmacia: Farmacia | None = db.query(Farmacia).filter(Farmacia.cnpj == cnpj_padrao).first()

        if not farmacia:
            farmacia = Farmacia(
                cnpj=cnpj_padrao,
                razao_social="Drogaria Araujo S.A",
                nome_fantasia="Araujo",
                endereco_completo="Extração via HTML Scraper"
            )
            db.add(instance=farmacia)
            db.commit()
            db.refresh(instance=farmacia)

        for prod in produtos:
            try:
                prod_validado = ProdutoExtraidoSchema.model_validate(prod)
            except ValidationError as e:
                print(f"[AVISO] Ignorando produto inválido: {e}")
                continue

            ean_validado = prod_validado.ean
            sku_interno = prod_validado.sku_interno

            if ean_validado and validar_ean13(ean=ean_validado):
                catalogo_item: CatalogoBase | None = db.query(CatalogoBase).filter(CatalogoBase.codigo_barras == ean_validado).first()
            else:
                catalogo_item = None
                ean_validado = None

            if not catalogo_item:
                # ---> NOVO: Executa o enriquecimento do dado antes de criar <---
                # Como salvar_no_banco é síncrono e roda em uma thread, precisamos rodar a corrotina
                ean_para_enriquecer = ean_validado if ean_validado else ""
                dados_enriquecidos = asyncio.run(
                    ServicoEnriquecimentoFarmacologico.enriquecer_produto(ean_para_enriquecer, prod_validado.name_search)
                )

                catalogo_item = CatalogoBase(
                    codigo_barras=ean_validado,
                    name_search=prod_validado.name_search,
                    principio_ativo=dados_enriquecidos['principio_ativo'],
                    laboratorio=dados_enriquecidos['laboratorio'],
                    exige_receita=dados_enriquecidos['exige_receita'],
                    categorias=dados_enriquecidos['categorias']
                )
                db.add(instance=catalogo_item)
                db.commit()
                db.refresh(instance=catalogo_item)

            oferta_existente = db.query(OfertaFarmacia).filter(
                OfertaFarmacia.url_origem == prod_validado.link
            ).first()

            if not oferta_existente:
                oferta_existente: OfertaFarmacia | None = db.query(OfertaFarmacia).filter(
                    OfertaFarmacia.catalogo_id == catalogo_item.id,
                    OfertaFarmacia.farmacia_id == farmacia.id
                ).first()

            if not oferta_existente:
                nova_oferta = OfertaFarmacia(
                    sku_interno=sku_interno,
                    preco=prod_validado.preco,
                    quantidade_estoque=1,
                    disponivel=True,
                    url_origem=prod_validado.link,
                    imagem_url=prod_validado.imagem_url,
                    farmacia_id=farmacia.id,
                    catalogo_id=catalogo_item.id
                )
                db.add(instance=nova_oferta)
            else:
                oferta_existente.preco = prod_validado.preco
                
                if oferta_existente.url_origem != prod_validado.link:
                    oferta_existente.url_origem = prod_validado.link
                    
                if prod_validado.imagem_url:
                    oferta_existente.imagem_url = prod_validado.imagem_url
            
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        print(f"[ERRO DB] Falha na persistência: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Iniciando varredura na Drogaria Araujo via HTML...")
    try:
        asyncio.run(main=extrair_todos_produtos())
    except KeyboardInterrupt:
        print("\nInterrompido pela usuária.")