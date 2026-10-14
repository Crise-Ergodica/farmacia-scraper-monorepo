"""Enriquecimento farmacológico com atributos de origem oficial explícita."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.anvisa import AnvisaMedicamento


class ServicoEnriquecimentoFarmacologico:
    _cache_ean: dict[str, dict[str, Any]] = {}

    @classmethod
    def enriquecer_lote(cls, db: Session, produtos: list[dict]) -> list[dict]:
        eans = {p["validado"].ean for p in produtos if p["validado"].ean}
        for ean in eans - cls._cache_ean.keys():
            cls._cache_ean[ean] = {}
        missing = [ean for ean in eans if not cls._cache_ean[ean]]
        if missing:
            for row in db.query(AnvisaMedicamento).filter(
                AnvisaMedicamento.ean.in_(missing)
            ):
                cls._cache_ean[row.ean] = cls._row_data(row)
        for product in produtos:
            validated = product["validado"]
            product["enriquecido"] = cls._result(
                cls._cache_ean.get(validated.ean, {}) if validated.ean else {},
                validated.name_search,
            )
        return produtos

    @classmethod
    def enriquecer_produto(
        cls, db: Session, ean: str, nome_comercial: str
    ) -> dict[str, Any]:
        if ean and ean not in cls._cache_ean:
            row = (
                db.query(AnvisaMedicamento).filter(AnvisaMedicamento.ean == ean).first()
            )
            cls._cache_ean[ean] = cls._row_data(row) if row else {}
        return cls._result(cls._cache_ean.get(ean, {}) if ean else {}, nome_comercial)

    @staticmethod
    def _row_data(row: AnvisaMedicamento) -> dict[str, Any]:
        return {
            "principio_ativo": row.principio_ativo,
            "laboratorio": row.laboratorio,
            "categoria_regulatoria": row.categoria_regulatoria,
            "referencia_anvisa": row.referencia_anvisa,
            "exige_receita_confirmada": row.exige_receita_confirmada,
            "controle_especial": row.controle_especial,
            "classificacao_fonte": row.fonte_classificacao,
        }

    @staticmethod
    def _result(data: dict[str, Any], name: str) -> dict[str, Any]:
        confirmed = data.get("exige_receita_confirmada")
        return {
            "principio_ativo": data.get("principio_ativo")
            or "Não informado (Pendente)",
            "laboratorio": data.get("laboratorio") or "Não informado",
            "categorias": [],
            "categoria_regulatoria": data.get("categoria_regulatoria"),
            "referencia_anvisa": data.get("referencia_anvisa"),
            "exige_receita_confirmada": confirmed,
            "controle_especial": data.get("controle_especial"),
            "classificacao_fonte": data.get("classificacao_fonte"),
            # Legacy contract remains boolean. Unknown is never used by new filters.
            "exige_receita": confirmed is True,
        }
