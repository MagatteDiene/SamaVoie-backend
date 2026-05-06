"""referentiels_et_profil_structure

Remplace le schéma partiellement JSON par un modèle 100 % relationnel :
  - Supprime users.niveau, users.serie, table user_interets (migration b2c4...)
  - Crée niveaux, series, interets (référentiels), profiles (1:1 users),
    profile_interets (N:M)
  - Pré-peuple les référentiels avec les données du système scolaire sénégalais

Revision ID: c3d5e7f9a0b2
Revises: b2c4d6e8f0a1
Create Date: 2026-05-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d5e7f9a0b2"
down_revision: Union[str, Sequence[str], None] = "b2c4d6e8f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Données de référence ──────────────────────────────────────────────────────

NIVEAUX = [
    {"id": 1,  "designation": "3ème",          "description": "Classe de Troisième (collège), année du BFEM"},
    {"id": 2,  "designation": "Seconde",        "description": "Classe de Seconde (lycée), 1re année du second cycle"},
    {"id": 3,  "designation": "Première",       "description": "Classe de Première (lycée)"},
    {"id": 4,  "designation": "Terminale",      "description": "Classe de Terminale (lycée), année du Baccalauréat"},
    {"id": 5,  "designation": "BTS / DUT",      "description": "Brevet de Technicien Supérieur ou Diplôme Universitaire de Technologie (Bac+2)"},
    {"id": 6,  "designation": "Licence 1 (L1)", "description": "Première année de licence universitaire (Bac+1)"},
    {"id": 7,  "designation": "Licence 2 (L2)", "description": "Deuxième année de licence universitaire (Bac+2)"},
    {"id": 8,  "designation": "Licence 3 (L3)", "description": "Troisième année de licence, diplôme Bac+3"},
    {"id": 9,  "designation": "Master 1 (M1)",  "description": "Première année de master (Bac+4)"},
    {"id": 10, "designation": "Master 2 (M2)",  "description": "Deuxième année de master, diplôme Bac+5"},
    {"id": 11, "designation": "Doctorat",       "description": "Cycle doctoral (Bac+8 et au-delà)"},
    {"id": 12, "designation": "Autre",          "description": "Autre niveau ou formation spécifique"},
]

SERIES = [
    {"id": 1,  "designation": "S1",   "description": "Mathématiques et Sciences Physiques"},
    {"id": 2,  "designation": "S2",   "description": "Sciences de la Vie et de la Terre (SVT)"},
    {"id": 3,  "designation": "S1A",  "description": "Sciences Appliquées et Technologie Agricole"},
    {"id": 4,  "designation": "S2A",  "description": "Sciences Appliquées et Agriculture"},
    {"id": 5,  "designation": "L1",   "description": "Langues et Sciences Humaines (français)"},
    {"id": 6,  "designation": "L2",   "description": "Lettres Modernes"},
    {"id": 7,  "designation": "L'1",  "description": "Langues et Lettres Arabes"},
    {"id": 8,  "designation": "G",    "description": "Sciences Économiques et Sociales"},
    {"id": 9,  "designation": "T1",   "description": "Sciences et Technologies Industrielles"},
    {"id": 10, "designation": "T2",   "description": "Techniques Économiques"},
    {"id": 11, "designation": "STEG", "description": "Sciences et Technologies de l'Économie et de la Gestion"},
    {"id": 12, "designation": "F4",   "description": "Sciences Informatiques et Mathématiques"},
    {"id": 13, "designation": "Autre","description": "Autre série ou formation non-Bac"},
]

INTERETS = [
    {"id": 1,  "designation": "Informatique & Numérique",      "description": "Développement logiciel, réseaux, cybersécurité, intelligence artificielle, data science"},
    {"id": 2,  "designation": "Médecine & Santé",              "description": "Médecine générale, pharmacie, odontologie, sciences infirmières, santé publique"},
    {"id": 3,  "designation": "Droit & Sciences Politiques",   "description": "Droit civil, droit des affaires, sciences politiques, diplomatie, administration"},
    {"id": 4,  "designation": "Commerce & Marketing",          "description": "Gestion commerciale, marketing digital, entrepreneuriat, e-commerce"},
    {"id": 5,  "designation": "Économie & Finance",            "description": "Économie, comptabilité, banque, assurance, finance d'entreprise"},
    {"id": 6,  "designation": "Ingénierie & BTP",              "description": "Génie civil, mécanique, électrique, bâtiment, travaux publics, énergie"},
    {"id": 7,  "designation": "Agriculture & Environnement",   "description": "Agronomie, élevage, pêche, environnement, développement durable"},
    {"id": 8,  "designation": "Arts & Communication",          "description": "Journalisme, communication, arts visuels, audiovisuel, design graphique"},
    {"id": 9,  "designation": "Sciences de l'Éducation",       "description": "Enseignement, formation, pédagogie, psychologie de l'éducation"},
    {"id": 10, "designation": "Langues & Lettres",             "description": "Linguistique, traduction, interprétariat, littérature, FLE"},
    {"id": 11, "designation": "Sciences Sociales",             "description": "Sociologie, psychologie, anthropologie, géographie humaine"},
    {"id": 12, "designation": "Mathématiques & Physique",      "description": "Mathématiques fondamentales, physique théorique, recherche scientifique"},
    {"id": 13, "designation": "Transport & Logistique",        "description": "Logistique, supply chain, transport maritime, aérien et terrestre"},
    {"id": 14, "designation": "Hôtellerie & Tourisme",         "description": "Tourisme, restauration, hôtellerie, gestion d'établissements"},
    {"id": 15, "designation": "Architecture & Urbanisme",      "description": "Architecture, urbanisme, aménagement du territoire, design intérieur"},
]


def upgrade() -> None:
    # ── Nettoyer le travail partiel de b2c4d6e8f0a1 ──────────────────────────
    op.drop_index("ix_user_interets_user_id", table_name="user_interets")
    op.drop_table("user_interets")
    op.drop_column("users", "serie")
    op.drop_column("users", "niveau")

    # ── Référentiels ──────────────────────────────────────────────────────────
    niveaux_table = op.create_table(
        "niveaux",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("designation"),
    )

    series_table = op.create_table(
        "series",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("designation"),
    )

    interets_table = op.create_table(
        "interets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("designation", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("designation"),
    )

    # ── Profil utilisateur ────────────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ville", sa.String(length=100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("niveau_id", sa.Integer(), nullable=True),
        sa.Column("serie_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["niveau_id"], ["niveaux.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["serie_id"], ["series.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    # ── Table de liaison Profile ↔ Intérêt ───────────────────────────────────
    op.create_table(
        "profile_interets",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("interet_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["interet_id"], ["interets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id", "interet_id"),
    )

    # ── Seed : pré-peuplement des référentiels ────────────────────────────────
    op.bulk_insert(niveaux_table, NIVEAUX)
    op.bulk_insert(series_table, SERIES)
    op.bulk_insert(interets_table, INTERETS)

    # Synchroniser les séquences PostgreSQL après bulk_insert avec IDs explicites
    op.execute("SELECT setval('niveaux_id_seq', (SELECT MAX(id) FROM niveaux))")
    op.execute("SELECT setval('series_id_seq', (SELECT MAX(id) FROM series))")
    op.execute("SELECT setval('interets_id_seq', (SELECT MAX(id) FROM interets))")


def downgrade() -> None:
    op.drop_table("profile_interets")
    op.drop_index("ix_profiles_user_id", table_name="profiles")
    op.drop_table("profiles")
    op.drop_table("interets")
    op.drop_table("series")
    op.drop_table("niveaux")

    # Remet les colonnes supprimées au début de upgrade()
    op.add_column("users", sa.Column("niveau", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("serie", sa.String(length=50), nullable=True))
    op.create_table(
        "user_interets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("interet", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_interets_user_id", "user_interets", ["user_id"])
