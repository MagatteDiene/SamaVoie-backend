import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.filiere import Filiere
from app.schemas.filiere import FiliereRead

router = APIRouter()
logger = logging.getLogger("samavoie.api.filieres")


@router.get("/", response_model=dict)
async def list_filieres(
    niveau: Optional[str] = Query(None, description="Filtrer par niveau (ex: Licence, Master, BTS)"),
    search: Optional[str] = Query(None, description="Recherche dans le nom ou la description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Filiere)
    count_stmt = select(func.count()).select_from(Filiere)

    if niveau:
        stmt = stmt.where(Filiere.niveau.ilike(f"%{niveau}%"))
        count_stmt = count_stmt.where(Filiere.niveau.ilike(f"%{niveau}%"))

    if search:
        like = f"%{search}%"
        stmt = stmt.where(Filiere.nom.ilike(like) | Filiere.description.ilike(like))
        count_stmt = count_stmt.where(Filiere.nom.ilike(like) | Filiere.description.ilike(like))

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Filiere.nom).offset((page - 1) * page_size).limit(page_size)
    filieres = (await db.execute(stmt)).scalars().all()

    return {
        "success": True,
        "data": [FiliereRead.model_validate(f) for f in filieres],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": -(-total // page_size)},
    }


@router.get("/{filiere_id}", response_model=dict)
async def get_filiere(filiere_id: int, db: AsyncSession = Depends(get_db)):
    filiere = await db.get(Filiere, filiere_id)
    if filiere is None:
        raise HTTPException(status_code=404, detail="Filière introuvable")
    return {"success": True, "data": FiliereRead.model_validate(filiere)}
