"""
Módulo responsável por inferir e enriquecer dados farmacológicos.
"""
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.anvisa import AnvisaMedicamento

CATEGORIAS_VALIDAS = {'Generico', 'Original', 'Similar', 'Controlados', 'Venda livre', 'Indeterminado'}

class ServicoEnriquecimentoFarmacologico:
    # Cache em memória para evitar chamadas redundantes ao banco local durante a execução do scraper
    _cache_ean: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def enriquecer_lote(cls, db: Session, produtos: List[Dict]) -> List[Dict]:
        """
        Enriquece um lote de produtos de uma só vez realizando uma única consulta
        na base de dados local (Bulk Lookup) para os EANs fornecidos.
        """
        # Extrai todos os eans válidos da lista de produtos
        lista_eans = [p["validado"].ean for p in produtos if p["validado"].ean]

        # Filtra os que não estão no cache e remove duplicatas
        eans_para_buscar = list(set([ean for ean in lista_eans if ean not in cls._cache_ean]))

        # Busca no banco apenas os EANs não cacheados (Bulk Lookup)
        if eans_para_buscar:
            registros = db.query(AnvisaMedicamento).filter(AnvisaMedicamento.ean.in_(eans_para_buscar)).all()
            for registro in registros:
                cls._cache_ean[registro.ean] = {
                    "principio_ativo": registro.principio_ativo,
                    "laboratorio": registro.laboratorio,
                    "tarja": registro.tarja,
                }

        # Itera sobre os produtos e aplica o enriquecimento
        for produto in produtos:
            prod_validado = produto["validado"]
            ean = prod_validado.ean
            nome_comercial = prod_validado.name_search

            if not ean:
                produto["enriquecido"] = cls._aplicar_fallback_restritivo(nome_comercial)
                continue

            dados_anvisa = cls._cache_ean.get(ean)

            if dados_anvisa and dados_anvisa.get("principio_ativo"):
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

                # Salva o resultado final no cache para evitar recálculo (opcional, já que cacheamos o dado cru)
                cls._cache_ean[f"{ean}_resultado"] = resultado
                produto["enriquecido"] = resultado
            else:
                produto["enriquecido"] = cls._aplicar_fallback_restritivo(nome_comercial)

        return produtos

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