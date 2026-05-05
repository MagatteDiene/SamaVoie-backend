import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.etablissement import Etablissement
from app.schemas.etablissement import EtablissementRead

router = APIRouter()
logger = logging.getLogger("samavoie.api.etablissements")


@router.get("/", response_model=dict)
async def list_etablissements(
    ville: Optional[str] = Query(None, description="Filtrer par ville/localisation"),
    type: Optional[str] = Query(None, description="Filtrer par type (Université, École, Institut…)"),
    search: Optional[str] = Query(None, description="Recherche dans le nom ou les formations"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Etablissement)
    count_stmt = select(func.count()).select_from(Etablissement)

    if ville:
        stmt = stmt.where(Etablissement.localisation.ilike(f"%{ville}%"))
        count_stmt = count_stmt.where(Etablissement.localisation.ilike(f"%{ville}%"))

    if type:
        stmt = stmt.where(Etablissement.type.ilike(f"%{type}%"))
        count_stmt = count_stmt.where(Etablissement.type.ilike(f"%{type}%"))

    if search:
        like = f"%{search}%"
        stmt = stmt.where(Etablissement.nom.ilike(like))
        count_stmt = count_stmt.where(Etablissement.nom.ilike(like))

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Etablissement.nom).offset((page - 1) * page_size).limit(page_size)
    etablissements = (await db.execute(stmt)).scalars().all()

    return {
        "success": True,
        "data": [EtablissementRead.model_validate(e) for e in etablissements],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": -(-total // page_size)},
    }


@router.get("/{etablissement_id}", response_model=dict)
async def get_etablissement(etablissement_id: int, db: AsyncSession = Depends(get_db)):
    etab = await db.get(Etablissement, etablissement_id)
    if etab is None:
        raise HTTPException(status_code=404, detail="Établissement introuvable")
    return {"success": True, "data": EtablissementRead.model_validate(etab)}
