from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.core.database import get_db  # Assumindo que sua injeção de dependência do DB está aqui
from app.models import CatalogoBase
from app.schemas import CatalogoComOfertasOut

router = APIRouter(prefix="/catalogo", tags=["Catálogo de Produtos"])

@router.get("/", response_model=list[CatalogoComOfertasOut])
def listar_catalogo_completo(db: Session = Depends(get_db)):
    """
    Retorna todo o catálogo de medicamentos, incluindo as ofertas locais 
    ativas em cada farmácia.
    """
    # Cria a query carregando as ofertas junto com o catálogo (Eager Loading)
    stmt = select(CatalogoBase).options(selectinload(CatalogoBase.ofertas))
    
    # Executa a query no banco
    resultados = db.execute(stmt).scalars().all()
    
    return resultados