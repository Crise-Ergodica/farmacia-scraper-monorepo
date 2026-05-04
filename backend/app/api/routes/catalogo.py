from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.core.database import get_db  
from app import schemas
from app.models import CatalogoBase, HistoricoPreco
from app.schemas import CatalogoComOfertasOut, HistoricoOut

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

@router.get("/medicamentos/{id}/historico", response_model=list[schemas.HistoricoOut])
def ler_historico(id: int, db: Session = Depends(get_db)):
    # Retorna os preços ordenados por data para o gráfico
    return db.query(HistoricoPreco).filter(
        HistoricoPreco.medicamento_id == id
    ).order_by(HistoricoPreco.data_registro.asc()).all()