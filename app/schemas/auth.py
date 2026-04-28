from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List

class UserProfile(BaseModel):
    niveau_scolaire: Optional[str] = None
    serie: Optional[str] = None
    ville: Optional[str] = None
    domaines_interet: List[str] = []
    matieres_preferees: List[str] = []

class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    profile: Optional[UserProfile] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
