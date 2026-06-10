from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.auth import fastapi_users, auth_backend, current_active_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.catalogo import CatalogoBase
from app.models.farmacia import Farmacia
from app.schemas.usuario import UsuarioRead, UsuarioCreate, UsuarioUpdate
from app.schemas.catalogo import CatalogoBaseSchema
from app.schemas.farmacia import FarmaciaOut

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

@router.post("/users/me/favoritos/medicamentos/{medicamento_id}", status_code=status.HTTP_201_CREATED)
def add_medicamento_favorito(
    medicamento_id: int,
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    medicamento = db.get(CatalogoBase, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado.")

    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.medicamentos_favoritos)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if any(m.id == medicamento_id for m in user_db.medicamentos_favoritos):
        raise HTTPException(status_code=400, detail="Medicamento já está nos favoritos.")

    user_db.medicamentos_favoritos.append(medicamento)
    db.commit()
    return {"message": "Medicamento adicionado aos favoritos."}

@router.delete("/users/me/favoritos/medicamentos/{medicamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_medicamento_favorito(
    medicamento_id: int,
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.medicamentos_favoritos)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    medicamento_to_remove = next((m for m in user_db.medicamentos_favoritos if m.id == medicamento_id), None)
    if not medicamento_to_remove:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado nos favoritos.")

    user_db.medicamentos_favoritos.remove(medicamento_to_remove)
    db.commit()

@router.get("/users/me/favoritos/medicamentos", response_model=list[CatalogoBaseSchema])
def list_medicamentos_favoritos(
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.medicamentos_favoritos)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    return user_db.medicamentos_favoritos

@router.post("/users/me/favoritos/farmacias/{farmacia_id}", status_code=status.HTTP_201_CREATED)
def add_farmacia_favorita(
    farmacia_id: int,
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    farmacia = db.get(Farmacia, farmacia_id)
    if not farmacia:
        raise HTTPException(status_code=404, detail="Farmácia não encontrada.")

    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.farmacias_favoritas)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if any(f.id == farmacia_id for f in user_db.farmacias_favoritas):
        raise HTTPException(status_code=400, detail="Farmácia já está nos favoritos.")

    user_db.farmacias_favoritas.append(farmacia)
    db.commit()
    return {"message": "Farmácia adicionada aos favoritos."}

@router.delete("/users/me/favoritos/farmacias/{farmacia_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_farmacia_favorita(
    farmacia_id: int,
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.farmacias_favoritas)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    farmacia_to_remove = next((f for f in user_db.farmacias_favoritas if f.id == farmacia_id), None)
    if not farmacia_to_remove:
        raise HTTPException(status_code=404, detail="Farmácia não encontrada nos favoritos.")

    user_db.farmacias_favoritas.remove(farmacia_to_remove)
    db.commit()

@router.get("/users/me/favoritos/farmacias", response_model=list[FarmaciaOut])
def list_farmacias_favoritas(
    user: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    user_db = db.get(Usuario, user.id, options=[joinedload(Usuario.farmacias_favoritas)])
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    return user_db.farmacias_favoritas