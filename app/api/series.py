from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.serie import Serie
from app.schemas.referentiel import SerieRead

router = APIRouter()


@router.get("/", response_model=list[SerieRead])
async def list_series(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Serie).order_by(Serie.id))
    return result.scalars().all()


@router.get("/{serie_id}", response_model=SerieRead)
async def get_serie(serie_id: int, db: AsyncSession = Depends(get_db)):
    serie = await db.get(Serie, serie_id)
    if serie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Série introuvable")
    return serie
