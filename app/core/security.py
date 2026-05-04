"""
Utilitaires de sécurité : hachage des mots de passe et tokens JWT.

Ce module est l'UNIQUE point d'accès aux fonctions cryptographiques.
Utilisé par app/api/auth.py et app/dependencies.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Retourne le hash bcrypt du mot de passe en clair."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond à son hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Génère un token JWT signé avec la clé secrète.

    Le champ 'sub' doit contenir l'email de l'utilisateur.
    La durée par défaut est ACCESS_TOKEN_EXPIRE_MINUTES (settings).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
