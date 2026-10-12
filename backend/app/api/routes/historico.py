from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CatalogoBase, Farmacia, HistoricoPreco
from app.schemas import (
    MedicineHistoryResponse,
    PharmacyHistorySchema,
    PricePointSchema,
)
from app.schemas.historico import PharmacyHistoryStatistics

router = APIRouter(prefix="/medicines", tags=["Price History"])
Period = Literal["7d", "30d", "90d", "6m", "1y", "all"]


def _period_start(period: Period) -> datetime | None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    durations = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "6m": timedelta(days=183),
        "1y": timedelta(days=365),
    }
    duration = durations.get(period)
    return now - duration if duration else None


@router.get("/{medicamento_id}/history", response_model=MedicineHistoryResponse)
def get_medicine_history(
    medicamento_id: int,
    periodo: Period = Query("all"),
    farmacia_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    if db.get(CatalogoBase, medicamento_id) is None:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado.")

    total_statement = select(func.count()).select_from(HistoricoPreco).where(
        HistoricoPreco.medicamento_id == medicamento_id
    )
    if farmacia_id is not None:
        total_statement = total_statement.where(
            HistoricoPreco.farmacia_id == farmacia_id
        )
    total_observacoes = db.execute(total_statement).scalar_one()

    statement = (
        select(HistoricoPreco, Farmacia.nome_fantasia)
        .join(Farmacia, HistoricoPreco.farmacia_id == Farmacia.id)
        .where(HistoricoPreco.medicamento_id == medicamento_id)
        .order_by(HistoricoPreco.data_registro.asc(), HistoricoPreco.id.asc())
    )
    start = _period_start(periodo)
    if start:
        statement = statement.where(HistoricoPreco.data_registro >= start)
    if farmacia_id is not None:
        statement = statement.where(HistoricoPreco.farmacia_id == farmacia_id)

    grouped: dict[int, dict] = {}
    for event, pharmacy_name in db.execute(statement).all():
        bucket = grouped.setdefault(
            event.farmacia_id,
            {
                "farmacia_id": event.farmacia_id,
                "pharmacy_name": pharmacy_name,
                "history": [],
            },
        )
        bucket["history"].append(
            PricePointSchema(
                preco=event.preco,
                data_registro=event.data_registro,
                oferta_id=event.oferta_id,
                origem=event.origem,
                disponivel=event.disponivel,
            )
        )

    pharmacies = []
    statistics = {}
    for pharmacy_id, data in grouped.items():
        points = data["history"]
        pharmacies.append(PharmacyHistorySchema(**data))
        values = [point.preco for point in points]
        first, last = values[0], values[-1]
        difference = last - first
        statistics[pharmacy_id] = PharmacyHistoryStatistics(
            farmacia_id=pharmacy_id,
            menor_preco=min(values),
            maior_preco=max(values),
            preco_medio=(sum(values, Decimal("0")) / len(values)).quantize(
                Decimal("0.01")
            ),
            primeiro_preco=first,
            ultimo_preco=last,
            variacao_absoluta=difference,
            variacao_percentual=(difference / first * 100).quantize(Decimal("0.01"))
            if first and len(values) > 1
            else None,
            primeira_observacao=points[0].data_registro,
            ultima_observacao=points[-1].data_registro,
        )

    pharmacies.sort(key=lambda pharmacy: pharmacy.farmacia_id)
    return MedicineHistoryResponse(
        medicamento_id=medicamento_id,
        pharmacies=pharmacies,
        periodo=periodo,
        total_observacoes=total_observacoes,
        statistics=statistics,
    )
