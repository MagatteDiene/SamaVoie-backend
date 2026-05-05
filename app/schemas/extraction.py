from pydantic import BaseModel, field_validator
from typing import Any, List, Optional


class MetierExtrait(BaseModel):
    nom: str
    description: str = ""
    competences: List[str] = []
    salaire_moyen: Optional[int] = None
    salaire_debutant: Optional[int] = None
    salaire_experimente: Optional[int] = None
    secteur: str = ""

    @field_validator("salaire_moyen", "salaire_debutant", "salaire_experimente", mode="before")
    @classmethod
    def valider_salaire_fcfa(cls, v):
        if v is None:
            return None
        try:
            vi = int(v)
        except (TypeError, ValueError):
            return None
        # Rejette les valeurs hors plage réaliste (attrape hallucinations : 43% → 43)
        if not (150_000 <= vi <= 6_000_000):
            return None
        return vi

    @field_validator("competences", mode="before")
    @classmethod
    def coerce_competences(cls, v):
        return _to_str_list(v)


class EtablissementExtrait(BaseModel):
    nom: str
    type: str = ""
    localisation: str = ""
    formations: List[str] = []
    conditions_admission: Optional[str] = None
    contact: Optional[str] = None

    @field_validator("formations", mode="before")
    @classmethod
    def coerce_formations(cls, v):
        return _to_str_list(v)


class FiliereExtraite(BaseModel):
    nom: str
    niveau: str = ""
    description: str = ""
    matieres: List[str] = []
    debouches: List[str] = []
    duree: str = ""
    etablissements: List[str] = []  # noms résolus après insertion
    metiers: List[str] = []         # noms résolus après insertion

    @field_validator("description", "niveau", "duree", mode="before")
    @classmethod
    def coerce_str(cls, v):
        return v if isinstance(v, str) else ""

    @field_validator("matieres", "debouches", mode="before")
    @classmethod
    def coerce_str_lists(cls, v):
        return _to_str_list(v)

    @field_validator("metiers", "etablissements", mode="before")
    @classmethod
    def coerce_name_lists(cls, v):
        # Le modèle renvoie parfois une string seule ou des objets complets
        # au lieu d'une liste de noms — on normalise dans les deux cas.
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, dict):
            return [v.get("nom", "")] if v.get("nom") else []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict) and item.get("nom"):
                    result.append(item["nom"])
            return result
        return []


class ExtractionResult(BaseModel):
    source: str                          # nom du fichier PDF
    filieres: List[FiliereExtraite] = []
    metiers: List[MetierExtrait] = []
    etablissements: List[EtablissementExtrait] = []
    chunks_texte: List[str] = []         # chunks pdfplumber pour indexation ChromaDB


# ---------------------------------------------------------------------------
# Utilitaire partagé
# ---------------------------------------------------------------------------

def _to_str_list(v: Any) -> List[str]:
    """Convertit n'importe quelle valeur en List[str] de manière tolérante."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, list):
        return [str(item) for item in v if item is not None]
    return []
