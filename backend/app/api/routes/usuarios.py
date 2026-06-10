from fastapi import APIRouter

from app.core.auth import fastapi_users, auth_backend
from app.schemas.usuario import UsuarioRead, UsuarioCreate, UsuarioUpdate

router = APIRouter(tags=["Usuários e Autenticação"])

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt"
)

router.include_router(
    fastapi_users.get_register_router(UsuarioRead, UsuarioCreate),
    prefix="/auth"
)

router.include_router(
    fastapi_users.get_users_router(UsuarioRead, UsuarioUpdate),
    prefix="/users"
)


from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import current_active_user
from app.models.usuario import Usuario
from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.schemas.catalogo import CatalogoBaseSchema
from app.schemas.farmacia import FarmaciaOut

@router.post("/users/me/favoritos/medicamentos/{medicamento_id}", status_code=status.HTTP_201_CREATED)
async def add_medicamento_favorito(
    medicamento_id: int,
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    medicamento = await db.get(CatalogoBase, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado.")

    # Needs to eagerly load favorites to check, or query associative table
    # Simple query for the associative table using relationships
    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["medicamentos_favoritos"])

    if any(m.id == medicamento_id for m in user_db.medicamentos_favoritos):
        raise HTTPException(status_code=400, detail="Medicamento já está nos favoritos.")

    user_db.medicamentos_favoritos.append(medicamento)
    await db.commit()
    return {"message": "Medicamento adicionado aos favoritos."}

@router.delete("/users/me/favoritos/medicamentos/{medicamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_medicamento_favorito(
    medicamento_id: int,
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["medicamentos_favoritos"])

    medicamento_to_remove = next((m for m in user_db.medicamentos_favoritos if m.id == medicamento_id), None)
    if not medicamento_to_remove:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado nos favoritos.")

    user_db.medicamentos_favoritos.remove(medicamento_to_remove)
    await db.commit()

@router.get("/users/me/favoritos/medicamentos", response_model=list[CatalogoBaseSchema])
async def list_medicamentos_favoritos(
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["medicamentos_favoritos"])

    return user_db.medicamentos_favoritos

@router.post("/users/me/favoritos/farmacias/{farmacia_id}", status_code=status.HTTP_201_CREATED)
async def add_farmacia_favorita(
    farmacia_id: int,
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    farmacia = await db.get(Farmacia, farmacia_id)
    if not farmacia:
        raise HTTPException(status_code=404, detail="Farmácia não encontrada.")

    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["farmacias_favoritas"])

    if any(f.id == farmacia_id for f in user_db.farmacias_favoritas):
        raise HTTPException(status_code=400, detail="Farmácia já está nos favoritos.")

    user_db.farmacias_favoritas.append(farmacia)
    await db.commit()
    return {"message": "Farmácia adicionada aos favoritos."}

@router.delete("/users/me/favoritos/farmacias/{farmacia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_farmacia_favorita(
    farmacia_id: int,
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["farmacias_favoritas"])

    farmacia_to_remove = next((f for f in user_db.farmacias_favoritas if f.id == farmacia_id), None)
    if not farmacia_to_remove:
        raise HTTPException(status_code=404, detail="Farmácia não encontrada nos favoritos.")

    user_db.farmacias_favoritas.remove(farmacia_to_remove)
    await db.commit()

@router.get("/users/me/favoritos/farmacias", response_model=list[FarmaciaOut])
async def list_farmacias_favoritas(
    user: Usuario = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Usuario).where(Usuario.id == user.id)
    result = await db.execute(stmt)
    user_db = result.scalars().first()
    await db.refresh(user_db, ["farmacias_favoritas"])

    return user_db.farmacias_favoritas
