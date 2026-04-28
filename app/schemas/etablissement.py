from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class EtablissementBase(BaseModel):
    nom: str
    type: str
    localisation: str
    formations: List[str] = []
    conditions_admission: Optional[str] = None
    contact: Optional[str] = None

class EtablissementCreate(EtablissementBase):
    pass

class EtablissementRead(EtablissementBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
