"""
Modelo de Usuário e tabelas associativas para favoritos.
"""
from sqlalchemy import Column, ForeignKey, String, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
import uuid

from .base import Base

usuario_medicamento_favorito = Table(
    "usuario_medicamento_favorito",
    Base.metadata,
    Column("usuario_id", GUID, ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("medicamento_id", Integer, ForeignKey("catalogo_base.id", ondelete="CASCADE"), primary_key=True),
)

usuario_farmacia_favorita = Table(
    "usuario_farmacia_favorita",
    Base.metadata,
    Column("usuario_id", GUID, ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("farmacia_id", Integer, ForeignKey("farmacias.id", ondelete="CASCADE"), primary_key=True),
)

class Usuario(SQLAlchemyBaseUserTableUUID, Base):
    """
    Modelo de Usuário para autenticação e gestão de favoritos.
    """
    __tablename__ = "usuario"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)

    medicamentos_favoritos: Mapped[list["CatalogoBase"]] = relationship(
        "CatalogoBase", secondary=usuario_medicamento_favorito
    )
    farmacias_favoritas: Mapped[list["Farmacia"]] = relationship(
        "Farmacia", secondary=usuario_farmacia_favorita
    )
