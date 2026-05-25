"""
Módulo responsável por inferir e enriquecer dados farmacológicos.
"""
import asyncio
from typing import Dict, Any

from app.core.database import SessionLocal
from app.models.anvisa import AnvisaMedicamento

CATEGORIAS_VALIDAS = {'Generico', 'Original', 'Similar', 'Controlados', 'Venda livre', 'Indeterminado'}

class ServicoEnriquecimentoFarmacologico:
    # Cache em memória para evitar chamadas redundantes ao banco local durante a execução do scraper
    _cache_ean: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _buscar_dados_por_ean_local(codigo_barras: str) -> Dict[str, Any]:
        """Realiza a busca síncrona na base local da ANVISA."""
        if not codigo_barras:
            return {}

        with SessionLocal() as db:
            registro = db.query(AnvisaMedicamento).filter_by(ean=codigo_barras).first()
            if registro:
                return {
                    "principio_ativo": registro.principio_ativo,
                    "laboratorio": registro.laboratorio,
                    "tarja": registro.tarja,
                }
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

        # 1. Verifica Cache (O(1) - Previne chamadas repetidas ao banco)
        if ean in cls._cache_ean:
            return cls._cache_ean[ean]

        # 2. Consulta banco local da ANVISA em uma thread separada para não bloquear o Event Loop
        dados_anvisa = await asyncio.to_thread(cls._buscar_dados_por_ean_local, ean)
        
        if dados_anvisa:
            descricao = dados_anvisa.get("principio_ativo") or nome_comercial
            marca = dados_anvisa.get("laboratorio") or "Não informado"
            tarja = (dados_anvisa.get("tarja") or "").lower()
            
            exige_receita = "vermelha" in tarja or "preta" in tarja
            
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
            
        # 3. Fallback Restritivo (se não encontrar na base da ANVISA, infere pelo nome e exige receita por segurança)
        resultado_fallback = cls._aplicar_fallback_restritivo(nome_comercial)
        cls._cache_ean[ean] = resultado_fallback # Adiciona resultados de fallback ao cache
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