import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.postgres import get_db
from app.dependencies import get_current_user
from app.models.interet import Interet
from app.models.niveau import Niveau
from app.models.profile import Profile
from app.models.serie import Serie
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter()
logger = logging.getLogger("samavoie.api.profiles")


async def _load_profile(user_id: int, db: AsyncSession) -> Optional[Profile]:
    """Charge le profil avec toutes ses relations imbriquées."""
    result = await db.execute(
        select(Profile)
        .options(
            joinedload(Profile.niveau),
            joinedload(Profile.serie),
            selectinload(Profile.interets),
        )
        .where(Profile.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.get("/me", response_model=ProfileRead)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _load_profile(current_user.id, db)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil non encore créé")
    return profile


@router.put("/me", response_model=ProfileRead)
async def upsert_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crée ou met à jour le profil de l'utilisateur connecté."""
    # Valider les FK avant de persister
    if data.niveau_id is not None and await db.get(Niveau, data.niveau_id) is None:
        raise HTTPException(status_code=422, detail=f"niveau_id={data.niveau_id} inexistant")
    if data.serie_id is not None and await db.get(Serie, data.serie_id) is None:
        raise HTTPException(status_code=422, detail=f"serie_id={data.serie_id} inexistant")

    # Charger les objets Interet pour les ids fournis
    interets: list[Interet] = []
    if data.interet_ids:
        result = await db.execute(select(Interet).where(Interet.id.in_(data.interet_ids)))
        interets = list(result.scalars().all())
        if len(interets) != len(set(data.interet_ids)):
            raise HTTPException(status_code=422, detail="Un ou plusieurs interet_ids sont invalides")

    # Charger ou créer le profil
    profile = await _load_profile(current_user.id, db)

    if profile is None:
        # Objet transient → tout passer au constructeur avant db.add()
        # (SQLAlchemy ne tente pas de charger les anciennes valeurs sur un objet transient)
        profile = Profile(
            user_id=current_user.id,
            ville=data.ville,
            bio=data.bio,
            niveau_id=data.niveau_id,
            serie_id=data.serie_id,
            interets=interets,
        )
        db.add(profile)
    else:
        # Objet persistent + interets déjà chargés via selectinload → safe
        profile.ville     = data.ville
        profile.bio       = data.bio
        profile.niveau_id = data.niveau_id
        profile.serie_id  = data.serie_id
        profile.interets  = interets

    await db.commit()

    # Recharger avec toutes les relations pour la réponse sérialisée
    return await _load_profile(current_user.id, db)
