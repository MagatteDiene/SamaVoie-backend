from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class MetierBase(BaseModel):
    nom: str
    description: str
    competences: List[str] = []
    salaire_moyen: Optional[int] = None
    salaire_debutant: Optional[int] = None
    salaire_experimente: Optional[int] = None
    secteur: str

class MetierCreate(MetierBase):
    pass

class MetierRead(MetierBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
