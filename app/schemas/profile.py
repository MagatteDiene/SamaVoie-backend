from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.referentiel import InteretRead, NiveauRead, SerieRead


class ProfileRead(BaseModel):
    id: int
    user_id: int
    ville: Optional[str] = None
    bio: Optional[str] = None
    niveau: Optional[NiveauRead] = None
    serie: Optional[SerieRead] = None
    interets: List[InteretRead] = []

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    """Payload pour créer ou mettre à jour le profil de l'utilisateur connecté."""
    ville: Optional[str] = None
    bio: Optional[str] = None
    niveau_id: Optional[int] = None
    serie_id: Optional[int] = None
    interet_ids: List[int] = []
