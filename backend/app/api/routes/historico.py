from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict

from app.core.database import get_db
from app.models import HistoricoPreco, Farmacia
from app.schemas import MedicineHistoryResponse, PharmacyHistorySchema, PricePointSchema

router = APIRouter(prefix="/medicines", tags=["Price History"])

@router.get("/{medicamento_id}/history", response_model=MedicineHistoryResponse)
def get_medicine_history(medicamento_id: int, db: Session = Depends(get_db)):
    """Fetches the price history of a specific medicine grouped by pharmacy.

    Args:
        medicamento_id: The ID of the medicine catalog item.
        db: The database session dependency.

    Returns:
        A MedicineHistoryResponse containing the medicine ID and its price history
        grouped by pharmacy.
    """
    historico_records = (
        db.query(HistoricoPreco, Farmacia.nome_fantasia)
        .join(Farmacia, HistoricoPreco.farmacia_id == Farmacia.id)
        .filter(HistoricoPreco.medicamento_id == medicamento_id)
        .order_by(HistoricoPreco.data_registro.asc())
        .all()
    )

    if not historico_records:
        return MedicineHistoryResponse(medicamento_id=medicamento_id, pharmacies=[])

    pharmacies_data = {}

    for hist, pharmacy_name in historico_records:
        farmacia_id = hist.farmacia_id

        if farmacia_id not in pharmacies_data:
            pharmacies_data[farmacia_id] = {
                "farmacia_id": farmacia_id,
                "pharmacy_name": pharmacy_name,
                "history": []
            }

        pharmacies_data[farmacia_id]["history"].append(
            PricePointSchema(
                preco=hist.preco,
                data_registro=hist.data_registro
            )
        )

    pharmacies_list = [
        PharmacyHistorySchema(**data) for data in pharmacies_data.values()
    ]

    return MedicineHistoryResponse(
        medicamento_id=medicamento_id,
        pharmacies=pharmacies_list
    )
