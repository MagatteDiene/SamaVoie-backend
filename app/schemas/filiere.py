from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class FiliereBase(BaseModel):
    nom: str
    niveau: str
    description: str
    matieres: List[str] = []
    debouches: List[str] = []
    duree: str

class FiliereCreate(FiliereBase):
    pass

class FiliereRead(FiliereBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
