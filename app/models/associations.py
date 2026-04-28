from sqlalchemy import Column, ForeignKey, Table
from app.db.postgres import Base

# Association entre Filière et Établissement
filiere_etablissement = Table(
    "filiere_etablissement",
    Base.metadata,
    Column("filiere_id", ForeignKey("filieres.id", ondelete="CASCADE"), primary_key=True),
    Column("etablissement_id", ForeignKey("etablissements.id", ondelete="CASCADE"), primary_key=True),
)

# Association entre Filière et Métier
filiere_metier = Table(
    "filiere_metier",
    Base.metadata,
    Column("filiere_id", ForeignKey("filieres.id", ondelete="CASCADE"), primary_key=True),
    Column("metier_id", ForeignKey("metiers.id", ondelete="CASCADE"), primary_key=True),
)
