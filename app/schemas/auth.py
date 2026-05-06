from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.profile import ProfileRead


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
    profile: Optional[ProfileRead] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
