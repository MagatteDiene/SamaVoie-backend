from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.interet import Interet
from app.schemas.referentiel import InteretRead

router = APIRouter()


@router.get("/", response_model=list[InteretRead])
async def list_interets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Interet).order_by(Interet.designation))
    return result.scalars().all()


@router.get("/{interet_id}", response_model=InteretRead)
async def get_interet(interet_id: int, db: AsyncSession = Depends(get_db)):
    interet = await db.get(Interet, interet_id)
    if interet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intérêt introuvable")
    return interet
