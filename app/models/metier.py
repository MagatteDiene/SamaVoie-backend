from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ARRAY
from app.db.postgres import Base
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.filiere import Filiere


class Metier(Base):
    __tablename__ = "metiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    competences: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    salaire_moyen: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salaire_debutant: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salaire_experimente: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    secteur: Mapped[str] = mapped_column(String(150), index=True, nullable=False)

    filieres: Mapped[List["Filiere"]] = relationship(
        "Filiere",
        secondary="filiere_metier",
        back_populates="metiers",
    )
