from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ARRAY
from app.db.postgres import Base
from app.models.associations import filiere_etablissement, filiere_metier
from typing import List

class Filiere(Base):
    __tablename__ = "filieres"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True)
    niveau: Mapped[str] = mapped_column(String(100)) # Licence, Master, BTS...
    description: Mapped[str] = mapped_column(Text)
    matieres: Mapped[List[str]] = mapped_column(ARRAY(String))
    debouches: Mapped[List[str]] = mapped_column(ARRAY(String))
    duree: Mapped[str] = mapped_column(String(50))

    # Relations N-N
    etablissements: Mapped[List["Etablissement"]] = relationship(
        secondary=filiere_etablissement, back_populates="filieres"
    )
    metiers: Mapped[List["Metier"]] = relationship(
        secondary=filiere_metier, back_populates="filieres"
    )

class Metier(Base):
    __tablename__ = "metiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    competences: Mapped[List[str]] = mapped_column(ARRAY(String))
    salaire_moyen: Mapped[int] = mapped_column(Integer, nullable=True)
    salaire_debutant: Mapped[int] = mapped_column(Integer, nullable=True)
    salaire_experimente: Mapped[int] = mapped_column(Integer, nullable=True)
    secteur: Mapped[str] = mapped_column(String(150), index=True)

    # Relation N-N
    filieres: Mapped[List["Filiere"]] = relationship(
        secondary=filiere_metier, back_populates="metiers"
    )

class Etablissement(Base):
    __tablename__ = "etablissements"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[str] = mapped_column(String(100)) # Université, Ecole...
    localisation: Mapped[str] = mapped_column(String(255))
    formations: Mapped[List[str]] = mapped_column(ARRAY(String))
    conditions_admission: Mapped[str] = mapped_column(Text, nullable=True)
    contact: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relation N-N
    filieres: Mapped[List["Filiere"]] = relationship(
        secondary=filiere_etablissement, back_populates="etablissements"
    )
