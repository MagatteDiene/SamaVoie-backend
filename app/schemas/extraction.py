from pydantic import BaseModel, field_validator
from typing import List, Optional


class MetierExtrait(BaseModel):
    nom: str
    description: str
    competences: List[str] = []
    salaire_moyen: Optional[int] = None
    salaire_debutant: Optional[int] = None
    salaire_experimente: Optional[int] = None
    secteur: str

    @field_validator("salaire_moyen", "salaire_debutant", "salaire_experimente", mode="before")
    @classmethod
    def valider_salaire_fcfa(cls, v):
        # Rejette toute valeur hors de la plage réaliste du marché sénégalais
        # Cela attrape les hallucinations Gemini (ex: confondre 43% avec 43 FCFA)
        if v is not None and not (150_000 <= int(v) <= 6_000_000):
            raise ValueError(
                f"Salaire FCFA hors plage plausible (150 000 – 6 000 000) : {v}"
            )
        return v


class EtablissementExtrait(BaseModel):
    nom: str
    type: str
    localisation: str
    formations: List[str] = []
    conditions_admission: Optional[str] = None
    contact: Optional[str] = None


class FiliereExtraite(BaseModel):
    nom: str
    niveau: str
    description: str
    matieres: List[str] = []
    debouches: List[str] = []
    duree: str
    etablissements: List[str] = []  # noms résolus après insertion
    metiers: List[str] = []         # noms résolus après insertion


class ExtractionResult(BaseModel):
    source: str                          # nom du fichier PDF
    filieres: List[FiliereExtraite] = []
    metiers: List[MetierExtrait] = []
    etablissements: List[EtablissementExtrait] = []
    chunks_texte: List[str] = []         # chunks pdfplumber pour indexation ChromaDB
