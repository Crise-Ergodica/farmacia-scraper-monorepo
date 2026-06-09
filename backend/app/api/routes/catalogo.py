from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_

from app.core.database import get_db  
from app import schemas
from app.models import CatalogoBase, HistoricoPreco, OfertaFarmacia
from app.schemas import CatalogoComOfertasOut, HistoricoOut, CatalogoPageOut, CatalogoFiltrosOut

router = APIRouter(prefix="/catalogo", tags=["Catálogo de Produtos"])

@router.get(path="", response_model=CatalogoPageOut)
def listar_catalogo_completo(
    limit: int = Query(20, ge=1, le=100, description="Quantidade de itens por página"),
    offset: int = Query(0, ge=0, description="Número de itens a pular"),
    exige_receita: bool | None = Query(None, description="Filtra por necessidade de receita"),
    categoria: str | None = Query(None, description="Filtra por categoria do medicamento"),
    farmacia_id: int | None = Query(None, description="Filtra medicamentos com ofertas ativas na farmácia especificada"),
    termo_busca: str | None = Query(None, description="Busca por nome ou princípio ativo"),
    db: Session = Depends(get_db)
):
    """
    Retorna o catálogo de medicamentos paginado e filtrado,
    incluindo as ofertas locais ativas em cada farmácia.
    """
    stmt = select(CatalogoBase)

    if exige_receita is not None:
        stmt = stmt.where(CatalogoBase.exige_receita == exige_receita)

    if categoria:
        stmt = stmt.where(CatalogoBase.categorias.any(categoria))

    if farmacia_id is not None:
        stmt = stmt.where(
            CatalogoBase.ofertas.any(
                (OfertaFarmacia.farmacia_id == farmacia_id) & (OfertaFarmacia.disponivel == True)
            )
        )

    if termo_busca:
        search_pattern = f"%{termo_busca}%"
        stmt = stmt.where(
            or_(
                CatalogoBase.name_search.ilike(search_pattern),
                CatalogoBase.principio_ativo.ilike(search_pattern)
            )
        )

    # Conta o total antes de paginar
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(total_stmt).scalar() or 0

    # Adiciona paginação e Eager Loading das ofertas
    stmt = stmt.options(selectinload(CatalogoBase.ofertas)).limit(limit).offset(offset)
    
    resultados = db.execute(stmt).scalars().all()
    
    return CatalogoPageOut(
        total=total,
        limit=limit,
        offset=offset,
        items=resultados
    )

@router.get(path="/filtros/opcoes", response_model=CatalogoFiltrosOut)
def obter_opcoes_filtros(db: Session = Depends(get_db)):
    """
    Retorna as opções únicas disponíveis no banco para categorias, laboratórios
    e princípios ativos, ignorando valores nulos, em branco ou "Não informado".
    """
    # Categorias (unnest do array)
    stmt_categorias = select(func.unnest(CatalogoBase.categorias).label("categoria")).distinct()
    categorias = [
        c for c in db.execute(stmt_categorias).scalars().all()
        if c and c.strip() and c != "Não informado"
    ]

    # Laboratórios
    stmt_labs = select(CatalogoBase.laboratorio).distinct()
    laboratorios = [
        lab for lab in db.execute(stmt_labs).scalars().all()
        if lab and lab.strip() and lab != "Não informado"
    ]

    # Princípios ativos
    stmt_principios = select(CatalogoBase.principio_ativo).distinct()
    principios = [
        p for p in db.execute(stmt_principios).scalars().all()
        if p and p.strip() and p != "Não informado"
    ]

    return CatalogoFiltrosOut(
        categorias=sorted(categorias),
        laboratorios=sorted(laboratorios),
        principios_ativos=sorted(principios)
    )

@router.get(path="/medicamentos/{id}/historico", response_model=list[schemas.HistoricoOut])
def ler_historico(id: int, db: Session = Depends(get_db)):
    # Retorna os preços ordenados por data para o gráfico
    return db.query(HistoricoPreco).filter(
        HistoricoPreco.medicamento_id == id
    ).order_by(HistoricoPreco.data_registro.asc()).all()