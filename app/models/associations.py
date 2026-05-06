from sqlalchemy import Column, ForeignKey, Table
from app.db.postgres import Base

# Filière ↔ Établissement
filiere_etablissement = Table(
    "filiere_etablissement",
    Base.metadata,
    Column("filiere_id", ForeignKey("filieres.id", ondelete="CASCADE"), primary_key=True),
    Column("etablissement_id", ForeignKey("etablissements.id", ondelete="CASCADE"), primary_key=True),
)

# Filière ↔ Métier
filiere_metier = Table(
    "filiere_metier",
    Base.metadata,
    Column("filiere_id", ForeignKey("filieres.id", ondelete="CASCADE"), primary_key=True),
    Column("metier_id", ForeignKey("metiers.id", ondelete="CASCADE"), primary_key=True),
)

# Profile ↔ Intérêt  (N:M)
profile_interets = Table(
    "profile_interets",
    Base.metadata,
    Column("profile_id", ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("interet_id", ForeignKey("interets.id", ondelete="CASCADE"), primary_key=True),
)
