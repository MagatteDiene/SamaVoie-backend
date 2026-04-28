from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ARRAY
from app.db.postgres import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.metier import Metier
    from app.models.etablissement import Etablissement


class Filiere(Base):
    __tablename__ = "filieres"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    niveau: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    matieres: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    debouches: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    duree: Mapped[str] = mapped_column(String(50), nullable=False)

    etablissements: Mapped[List["Etablissement"]] = relationship(
        "Etablissement",
        secondary="filiere_etablissement",
        back_populates="filieres",
    )
    metiers: Mapped[List["Metier"]] = relationship(
        "Metier",
        secondary="filiere_metier",
        back_populates="filieres",
    )
