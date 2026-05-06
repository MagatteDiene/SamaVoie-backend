import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.postgres import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead

logger = logging.getLogger("samavoie.auth")
router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        nom=user_in.nom,
        prenom=user_in.prenom,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Nouvel utilisateur : %s (id=%d)", user.email, user.id)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez un administrateur.",
        )

    token = create_access_token(data={"sub": user.email})
    logger.info("Connexion réussie : %s (id=%d)", user.email, user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    # get_current_user charge déjà le profil avec ses relations imbriquées
    return current_user
