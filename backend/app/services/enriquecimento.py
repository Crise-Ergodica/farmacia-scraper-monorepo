"""
Módulo responsável por inferir e enriquecer dados farmacológicos.
Idealmente executado como um worker assíncrono (ex: Celery) ou em lote pós-scraping.
"""
import re
import httpx
from typing import Dict, Any, List

# Categorias mapeadas conforme contrato do Frontend
CATEGORIAS_VALIDAS = {'Generico', 'Original', 'Similar', 'Controlados', 'Venda livre'}

class ServicoEnriquecimentoFarmacologico:
            
    @staticmethod
    async def buscar_dados_por_ean(codigo_barras: str) -> Dict[str, Any]:
        """
        Consulta uma API externa (Mock para Cosmos/Bluesoft/BrasilAPI) 
        para obter dados mestres do produto usando o EAN.
        """
        # Exemplo prático de chamada HTTP (substitua pela API real escolhida)
        # url = f"https://api.cosmos.bluesoft.com.br/gtins/{codigo_barras}.json"
        # Em um cenário real, você injetaria seu token de API aqui.
        return {} # Mock: retornando vazio para forçar a heurística neste exemplo

    @staticmethod
    def aplicar_heuristica_nome(nome_comercial: str) -> Dict[str, Any]:
        """
        Gera metadados inferindo padrões comuns nos nomes comerciais das farmácias.
        Utilizado como fallback robusto contra falhas de API.
        """
        nome_lower = nome_comercial.lower()
        categorias: set[str] = set()
        exige_receita = False
        
        # 1. Identificação de Genéricos (Lei 9.787/99 exige a nomenclatura)
        if "genérico" in nome_lower or "generico" in nome_lower:
            categorias.add("Generico")
        
        # 2. Identificação de Controle Especial
        termos_controle = ["tarja preta", "tarja vermelha", "retenção de receita", "antibiótico", "psicotrópico"]
        if any(termo in nome_lower for termo in termos_controle):
            categorias.add("Controlados")
            exige_receita = True
            
        # 3. Classificação de Venda Livre (OTC)
        if not exige_receita and "Generico" not in categorias:
            # Assunção cética: se não explicitou controle, assumimos venda livre até atualização por API
            categorias.add("Venda livre")
            
        return {
            "categorias": list(categorias),
            "exige_receita": exige_receita,
            # Princípio e laboratório são perigosos de inferir por regex puro, 
            # mantemos o default caso não venha da API.
            "principio_ativo": "Não informado",
            "laboratorio": "Não informado"
        }

    @classmethod
    async def enriquecer_produto(cls, ean: str, nome: str) -> Dict[str, Any]:
        """
        Pipeline principal: Tenta dados determinísticos, cai para inferência em caso de falha.
        """
        # 1. Tenta API Externa
        dados_api = await cls.buscar_dados_por_ean(ean)
        
        if dados_api:
            # Mapeamento do payload da API para o modelo (Depende da resposta da sua API)
            return {
                "principio_ativo": dados_api.get("description", "Não informado"),
                "laboratorio": dados_api.get("brand", {}).get("name", "Não informado"),
                "categorias": ["Original"], # Exemplo de mapeamento
                "exige_receita": False
            }
            
        # 2. Fallback para Heurística de Texto
        return cls.aplicar_heuristica_nome(nome)