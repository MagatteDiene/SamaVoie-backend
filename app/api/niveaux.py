from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.niveau import Niveau
from app.schemas.referentiel import NiveauRead

router = APIRouter()


@router.get("/", response_model=list[NiveauRead])
async def list_niveaux(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Niveau).order_by(Niveau.id))
    return result.scalars().all()


@router.get("/{niveau_id}", response_model=NiveauRead)
async def get_niveau(niveau_id: int, db: AsyncSession = Depends(get_db)):
    niveau = await db.get(Niveau, niveau_id)
    if niveau is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Niveau introuvable")
    return niveau
