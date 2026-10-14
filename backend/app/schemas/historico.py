from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _assume_utc_for_naive_timestamp(value: datetime) -> datetime:
    """Database timestamps are stored without tzinfo but represent UTC instants."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class PricePointSchema(BaseModel):
    """Represents a price point in time for a medicine.

    Attributes:
        preco: The recorded price.
        data_registro: The datetime when the price was recorded.
    """

    preco: Decimal
    data_registro: datetime
    oferta_id: Optional[int] = None
    origem: Optional[str] = None
    disponivel: Optional[bool] = None

    @field_validator("data_registro")
    @classmethod
    def normalize_timestamp_timezone(cls, value: datetime) -> datetime:
        return _assume_utc_for_naive_timestamp(value)


class PharmacyHistorySchema(BaseModel):
    """Represents the price history of a specific medicine in a specific pharmacy.

    Attributes:
        farmacia_id: The ID of the pharmacy.
        pharmacy_name: The name of the pharmacy.
        history: A list of recorded price points.
    """

    farmacia_id: int
    pharmacy_name: Optional[str] = None
    history: list[PricePointSchema]


class PharmacyHistoryStatistics(BaseModel):
    farmacia_id: int
    menor_preco: Decimal
    maior_preco: Decimal
    preco_medio: Decimal
    primeiro_preco: Decimal
    ultimo_preco: Decimal
    variacao_absoluta: Decimal
    variacao_percentual: Decimal | None = None
    primeira_observacao: datetime
    ultima_observacao: datetime

    @field_validator("primeira_observacao", "ultima_observacao")
    @classmethod
    def normalize_observation_timezone(cls, value: datetime) -> datetime:
        return _assume_utc_for_naive_timestamp(value)


class MedicineHistoryResponse(BaseModel):
    """Response schema for the medicine price history endpoint.

    Attributes:
        medicamento_id: The ID of the medicine.
        pharmacies: A list of price histories grouped by pharmacy.
    """

    medicamento_id: int
    pharmacies: list[PharmacyHistorySchema]
    periodo: str = "all"
    total_observacoes: int = 0
    statistics: dict[int, PharmacyHistoryStatistics] = Field(default_factory=dict)
