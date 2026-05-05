import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.metier import Metier
from app.schemas.metier import MetierRead

router = APIRouter()
logger = logging.getLogger("samavoie.api.metiers")


@router.get("/", response_model=dict)
async def list_metiers(
    secteur: Optional[str] = Query(None, description="Filtrer par secteur d'activité"),
    search: Optional[str] = Query(None, description="Recherche dans le nom ou la description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Metier)
    count_stmt = select(func.count()).select_from(Metier)

    if secteur:
        stmt = stmt.where(Metier.secteur.ilike(f"%{secteur}%"))
        count_stmt = count_stmt.where(Metier.secteur.ilike(f"%{secteur}%"))

    if search:
        like = f"%{search}%"
        stmt = stmt.where(Metier.nom.ilike(like) | Metier.description.ilike(like))
        count_stmt = count_stmt.where(Metier.nom.ilike(like) | Metier.description.ilike(like))

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Metier.nom).offset((page - 1) * page_size).limit(page_size)
    metiers = (await db.execute(stmt)).scalars().all()

    return {
        "success": True,
        "data": [MetierRead.model_validate(m) for m in metiers],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": -(-total // page_size)},
    }


@router.get("/{metier_id}", response_model=dict)
async def get_metier(metier_id: int, db: AsyncSession = Depends(get_db)):
    metier = await db.get(Metier, metier_id)
    if metier is None:
        raise HTTPException(status_code=404, detail="Métier introuvable")
    return {"success": True, "data": MetierRead.model_validate(metier)}
