from typing import Optional, Any
import uuid
from fastapi_users import schemas
from pydantic import Field, field_validator

class UsuarioRead(schemas.BaseUser[uuid.UUID]):
    nome: str

class UsuarioCreate(schemas.BaseUserCreate):
    nome: str = Field(..., min_length=3, max_length=100)

    @field_validator('nome', mode='before')
    @classmethod
    def limpar_nome(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Nome não pode estar vazio")
        return v

class UsuarioUpdate(schemas.BaseUserUpdate):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
