from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ARRAY
from app.db.postgres import Base
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.filiere import Filiere


class Etablissement(Base):
    __tablename__ = "etablissements"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    localisation: Mapped[str] = mapped_column(String(255), nullable=False)
    formations: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    conditions_admission: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    filieres: Mapped[List["Filiere"]] = relationship(
        "Filiere",
        secondary="filiere_etablissement",
        back_populates="etablissements",
    )
