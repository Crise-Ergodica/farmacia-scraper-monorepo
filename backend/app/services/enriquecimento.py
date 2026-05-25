"""
Módulo responsável por inferir e enriquecer dados farmacológicos.
"""
import os
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env.example"

load_dotenv(dotenv_path=env_path)

CATEGORIAS_VALIDAS = {'Generico', 'Original', 'Similar', 'Controlados', 'Venda livre', 'Indeterminado'}

class ServicoEnriquecimentoFarmacologico:
    # Cache em memória para evitar chamadas redundantes à API externa durante a execução do scraper
    _cache_ean: Dict[str, Dict[str, Any]] = {}
            
    @staticmethod
    async def buscar_dados_por_ean(codigo_barras: str) -> Dict[str, Any]:
        token = os.getenv("API_EAN_TOKEN", "")
        # Adicione um log para verificar se o token está realmente chegando
        print(f"DEBUG: Consultando EAN: {codigo_barras} | Token len: {len(token)}")
        
        url = f"https://api.cosmos.bluesoft.com.br/gtins/{codigo_barras}.json"
        headers = {"X-Cosmos-Token": token, "User-Agent": "PrecoBao-Worker/1.0"}
        
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                resposta = await client.get(url, headers=headers)
                
                # DEBUG CRÍTICO: Ver o status e o corpo da resposta
                print(f"DEBUG: Status API: {resposta.status_code}")
                if resposta.status_code != 200:
                    print(f"DEBUG: Corpo da resposta (Erro): {resposta.text[:200]}")
                
                if resposta.status_code == 200:
                    return resposta.json()
                return {}
        except httpx.RequestError as e:
            print(f"[ERRO REDE] Falha ao consultar EAN {codigo_barras}: {e}")
            return {}

    @staticmethod
    def inferir_categoria_por_texto(texto: str, exige_receita: bool) -> list[str]:
        """Desacoplado para uso tanto na API quanto no fallback."""
        texto_lower = texto.lower()
        categorias = set()
        
        if "genérico" in texto_lower or "generico" in texto_lower:
            categorias.add("Generico")
        elif not exige_receita:
            categorias.add("Venda livre")
            
        return list(categorias) if categorias else ["Original"]

    @classmethod
    async def enriquecer_produto(cls, ean: str, nome_comercial: str) -> Dict[str, Any]:
        """
        Pipeline principal com Cache, API e Fallback.
        """
        if not ean:
            return cls._aplicar_fallback_restritivo(nome_comercial)

        # 1. Verifica Cache (O(1) - Previne bloqueio da API)
        if ean in cls._cache_ean:
            return cls._cache_ean[ean]

        # 2. Tenta API Externa real
        dados_api = await cls.buscar_dados_por_ean(ean)
        
        if dados_api:
            descricao = dados_api.get("description", nome_comercial)
            marca = dados_api.get("brand", {}).get("name", "Não informado")
            
            texto_regulatorio = str(dados_api).lower()
            exige_receita = "tarja vermelha" in texto_regulatorio or "tarja preta" in texto_regulatorio or "retenção" in texto_regulatorio
            
            # Combina a descrição oficial com o nome comercial da farmácia para não perder a detecção de Genérico
            contexto_texto = f"{descricao} {nome_comercial}"
            categorias_reais = cls.inferir_categoria_por_texto(contexto_texto, exige_receita)
            
            resultado = {
                "principio_ativo": descricao,
                "laboratorio": marca,
                "categorias": categorias_reais, 
                "exige_receita": exige_receita
            }
            
            # Salva no cache antes de retornar
            cls._cache_ean[ean] = resultado
            return resultado
            
        # 3. Fallback Restritivo (se falhar, exige receita por segurança)
        resultado_fallback = cls._aplicar_fallback_restritivo(nome_comercial)
        cls._cache_ean[ean] = resultado_fallback # Adiciona falhas ao cache para não insistir no mesmo EAN
        return resultado_fallback

    @staticmethod
    def _aplicar_fallback_restritivo(nome_comercial: str) -> Dict[str, Any]:
        """Garante a negação por defeito em caso de falha."""
        nome_lower = nome_comercial.lower()
        categorias: set[str] = set()
        exige_receita = False
        
        if "genérico" in nome_lower or "generico" in nome_lower:
            categorias.add("Generico")
        
        termos_controle = ["tarja preta", "tarja vermelha", "retenção de receita", "antibiótico", "psicotrópico"]
        if any(termo in nome_lower for termo in termos_controle):
            categorias.add("Controlados")
            exige_receita = True
            
        if not exige_receita and "Generico" not in categorias:
            categorias.add("Indeterminado")
            exige_receita = True 
            
        return {
            "categorias": list(categorias),
            "exige_receita": exige_receita,
            "principio_ativo": "Não informado (Pendente)",
            "laboratorio": "Não informado"
        }