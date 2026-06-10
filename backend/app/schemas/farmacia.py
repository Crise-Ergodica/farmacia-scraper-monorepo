from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class FarmaciaBaseSchema(BaseModel):
    cnpj: str = Field(..., max_length=14)
    razao_social: str = Field(..., max_length=150)
    nome_fantasia: str = Field(..., max_length=100)
    telefone: str | None = Field(None, max_length=20)
    endereco_completo: str = Field(..., max_length=255)
    latitude: Decimal | None = None
    longitude: Decimal | None = None

class FarmaciaOut(FarmaciaBaseSchema):
    id: int
    criado_em: datetime
    atualizado_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
