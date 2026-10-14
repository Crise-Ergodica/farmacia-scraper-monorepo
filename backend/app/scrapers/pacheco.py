"""
Scraper especializado para extração de dados da Drogaria Pacheco via API VTEX.

A Pacheco utiliza plataforma VTEX, que expõe uma API REST pública de catálogo
em ``/api/catalog_system/pub/products/search/medicamentos``. A paginação é
feita com os parâmetros ``_from`` e ``_to`` (base 0, inclusivo). Cada item
da resposta contém ``items[0]`` com EAN, imagens e ``sellers[0].commertialOffer``
com preço e disponibilidade.
"""

import asyncio
from typing import Any, Dict, List

from curl_cffi import requests

from app.scrapers.base import BasePharmacyScraper
from app.services.imagens import image_delivery_rejection_reason


class PachecoScraper(BasePharmacyScraper):
    """Scraper da Drogaria Pacheco consumindo a API VTEX de catálogo."""

    ITEMS_PER_PAGE = 50
    API_BASE = (
        "https://www.drogariaspacheco.com.br"
        "/api/catalog_system/pub/products/search/medicamentos"
    )

    def __init__(self, num_workers: int = 3, batch_size: int = 50):
        super().__init__(
            farmacia_cnpj="38792017000130",
            farmacia_razao_social="Drogarias Pacheco S.A.",
            farmacia_nome_fantasia="Pacheco",
            farmacia_endereco="Extração via API VTEX",
            num_workers=num_workers,
            batch_size=batch_size,
        )

    async def extrair_catalogo(self) -> None:
        """Itera sobre a API VTEX paginada e envia produtos para a fila."""
        offset = 0
        pagina = 1
        headers = {
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.drogariaspacheco.com.br/medicamentos",
        }

        async with requests.AsyncSession(
            impersonate="chrome110", verify=False, headers=headers
        ) as session:
            while True:
                end = offset + self.ITEMS_PER_PAGE - 1
                print(
                    f"Buscando Drogaria Pacheco - Página {pagina} "
                    f"(itens {offset}-{end})..."
                )

                try:
                    url = f"{self.API_BASE}?_from={offset}&_to={end}"

                    async def fetch():
                        return await session.get(url, timeout=30.0)

                    response = await self.executar_com_backoff(fetch)

                    # 404 ou lista vazia sinalizam fim do catálogo
                    if response.status_code == 404:
                        print("Fim do catálogo (404).")
                        break

                    if response.status_code not in (200, 206):
                        print(
                            f"Status inesperado {response.status_code}. "
                            "Encerrando varredura."
                        )
                        break

                    produtos_brutos = response.json()
                    if not produtos_brutos:
                        print("Lista vazia. Varredura finalizada.")
                        break

                    produtos_limpos = self._adaptar_resposta_api(produtos_brutos)

                    if not produtos_limpos:
                        print(
                            f"Nenhum produto válido na página {pagina}. "
                            "Varredura finalizada."
                        )
                        break

                    for prod in produtos_limpos:
                        await self.fila.put(prod)

                    print(
                        f"✓ {len(produtos_limpos)} medicamentos enfileirados "
                        f"da página {pagina}."
                    )

                    # Se retornou menos que o tamanho da página, é a última
                    if len(produtos_brutos) < self.ITEMS_PER_PAGE:
                        print("Última página atingida.")
                        break

                    offset += self.ITEMS_PER_PAGE
                    pagina += 1

                except Exception as e:
                    print(f"Falha inesperada no scraper da Pacheco: {e}")
                    break

    def _adaptar_resposta_api(
        self, produtos_brutos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Converte a resposta da API VTEX para o schema ProdutoExtraidoSchema."""
        catalogo: List[Dict[str, Any]] = []

        for item in produtos_brutos:
            try:
                produto = self._extrair_produto(item)
                if produto:
                    catalogo.append(produto)
            except Exception as e:
                nome = item.get("productName", "?")
                print(f"Erro ao adaptar produto '{nome}': {e}")
                continue

        return catalogo

    def _extrair_produto(self, item: Dict[str, Any]) -> Dict[str, Any] | None:
        """Extrai campos de um único item da API VTEX."""
        items = item.get("items")
        if not items:
            return None

        sku_data = items[0]
        sellers = sku_data.get("sellers")
        if not sellers:
            return None

        offer = sellers[0].get("commertialOffer", {})
        preco = offer.get("Price")
        if preco is None or preco <= 0:
            return None

        sku_id = str(sku_data.get("itemId") or item.get("productId") or "")
        if not sku_id:
            return None

        nome = sku_data.get("name") or item.get("productName") or ""
        ean = sku_data.get("ean") or None
        if isinstance(ean, str):
            ean = ean.strip().replace("-", "").replace(" ", "")
            if not ean:
                ean = None

        link_text = item.get("linkText") or ""
        link = (
            f"https://www.drogariaspacheco.com.br/{link_text}/p"
            if link_text
            else ""
        )

        imagem_url = self._extrair_imagem(sku_data)

        return {
            "id": sku_id,
            "sku_interno": f"PCH{sku_id}",
            "ean": ean,
            "name_search": nome[:150],
            "preco": float(preco),
            "link": link,
            "imagem_url": imagem_url,
        }

    @staticmethod
    def _extrair_imagem(sku_data: Dict[str, Any]) -> str | None:
        """Extrai a primeira imagem válida do SKU."""
        images = sku_data.get("images")
        if not images:
            return None

        for img in images:
            url = img.get("imageUrl")
            if not url:
                continue
            url = str(url)
            if url.startswith("//"):
                url = f"https:{url}"
            if image_delivery_rejection_reason(url):
                continue
            return url

        return None


if __name__ == "__main__":
    print("Iniciando varredura na Drogaria Pacheco via API VTEX...")
    scraper = PachecoScraper(num_workers=3, batch_size=50)
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\nInterrompido pela usuária.")