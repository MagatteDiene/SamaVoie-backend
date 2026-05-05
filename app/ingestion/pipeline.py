import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.embedding import load_embedding_model
from app.db.postgres import AsyncSessionLocal
from app.ingestion.bge_indexer import index_chunks
from app.ingestion.chunker import split_text
from app.ingestion.gemini_extractor import extract_from_pdf
from app.ingestion.pdf_utils import extract_text_from_pdf
from app.models.etablissement import Etablissement
from app.models.filiere import Filiere
from app.models.metier import Metier
from app.schemas.extraction import ExtractionResult

logger = logging.getLogger("samavoie.ingestion.pipeline")


# ---------------------------------------------------------------------------
# Helpers PostgreSQL (get-or-create idempotents)
# ---------------------------------------------------------------------------

async def _get_or_create_metier(db: AsyncSession, data) -> Metier:
    result = await db.execute(select(Metier).where(Metier.nom == data.nom))
    metier = result.scalar_one_or_none()

    if metier is None:
        metier = Metier(
            nom=data.nom,
            description=data.description,
            competences=data.competences,
            salaire_moyen=data.salaire_moyen,
            salaire_debutant=data.salaire_debutant,
            salaire_experimente=data.salaire_experimente,
            secteur=data.secteur,
        )
        db.add(metier)
    else:
        # Enrichissement progressif : ne remplace que les champs vides en base
        if not metier.description and data.description:
            metier.description = data.description
        if not metier.competences and data.competences:
            metier.competences = data.competences
        if metier.salaire_moyen is None and data.salaire_moyen is not None:
            metier.salaire_moyen = data.salaire_moyen
        if metier.salaire_debutant is None and data.salaire_debutant is not None:
            metier.salaire_debutant = data.salaire_debutant
        if metier.salaire_experimente is None and data.salaire_experimente is not None:
            metier.salaire_experimente = data.salaire_experimente
        if not metier.secteur and data.secteur:
            metier.secteur = data.secteur

    await db.flush()
    return metier


async def _get_or_create_etablissement(db: AsyncSession, data) -> Etablissement:
    result = await db.execute(select(Etablissement).where(Etablissement.nom == data.nom))
    etab = result.scalar_one_or_none()

    if etab is None:
        etab = Etablissement(
            nom=data.nom,
            type=data.type,
            localisation=data.localisation,
            formations=data.formations,
            conditions_admission=data.conditions_admission,
            contact=data.contact,
        )
        db.add(etab)
    else:
        # Enrichissement progressif : ne remplace que les champs vides en base
        if not etab.type and data.type:
            etab.type = data.type
        if not etab.localisation and data.localisation:
            etab.localisation = data.localisation
        if not etab.formations and data.formations:
            etab.formations = data.formations
        if etab.conditions_admission is None and data.conditions_admission:
            etab.conditions_admission = data.conditions_admission
        if etab.contact is None and data.contact:
            etab.contact = data.contact

    await db.flush()
    return etab


async def _save_to_postgres(result: ExtractionResult) -> dict:
    counts = {"filieres": 0, "metiers": 0, "etablissements": 0}

    async with AsyncSessionLocal() as db:
        metier_map: dict[str, Metier] = {}
        for m in result.metiers:
            metier_map[m.nom] = await _get_or_create_metier(db, m)
            counts["metiers"] += 1

        etab_map: dict[str, Etablissement] = {}
        for e in result.etablissements:
            etab_map[e.nom] = await _get_or_create_etablissement(db, e)
            counts["etablissements"] += 1

        for f in result.filieres:
            res = await db.execute(select(Filiere).where(Filiere.nom == f.nom))
            filiere = res.scalar_one_or_none()
            if filiere is None:
                filiere = Filiere(
                    nom=f.nom,
                    niveau=f.niveau,
                    description=f.description,
                    matieres=f.matieres,
                    debouches=f.debouches,
                    duree=f.duree,
                )
                db.add(filiere)
                await db.flush()

            for nom in f.metiers:
                if nom in metier_map and metier_map[nom] not in filiere.metiers:
                    filiere.metiers.append(metier_map[nom])
            for nom in f.etablissements:
                if nom in etab_map and etab_map[nom] not in filiere.etablissements:
                    filiere.etablissements.append(etab_map[nom])

            counts["filieres"] += 1

        await db.commit()

    return counts


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

async def run_pipeline(pdf_path: Path) -> ExtractionResult:
    """
    Pipeline hybride complet pour un PDF.

    Deux flux indépendants et complémentaires :

    Flux A — Structuré (Gemini Vision → PostgreSQL)
      Le PDF est envoyé directement à Gemini qui le lit visuellement.
      Gemini extrait filières, métiers, établissements en JSON validé par Pydantic.
      Les entités sont upsertées en PostgreSQL (idempotent).

    Flux B — Sémantique (pdfplumber → chunker → BGE-M3 → ChromaDB)
      pdfplumber extrait le texte en gérant les tableaux et la disposition slide deck.
      Le texte est découpé en chunks (≈512 tokens) puis encodé par BGE-M3.
      Les vecteurs sont upsertés dans ChromaDB (idempotent via source::index).

    Retourne l'ExtractionResult avec chunks_texte peuplé.
    """
    logger.info("=== Démarrage pipeline : %s ===", pdf_path.name)

    # BGE-M3 requis pour le Flux B — no-op si déjà chargé via lifespan FastAPI
    load_embedding_model()

    # --- Flux A : Gemini Vision → données structurées PostgreSQL ---
    extraction = await extract_from_pdf(pdf_path)

    # --- Flux B : pdfplumber → chunking → ChromaDB ---
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = split_text(raw_text)
    extraction.chunks_texte = chunks  # chunks disponibles dans l'objet retourné

    indexed = index_chunks(chunks, source=pdf_path.name)

    # --- Sauvegarde PostgreSQL (après chunks pour que l'objet soit complet) ---
    db_counts = await _save_to_postgres(extraction)

    logger.info(
        "=== Pipeline terminé : source=%s | chunks=%d | filieres=%d | metiers=%d | etablissements=%d ===",
        pdf_path.name, indexed,
        db_counts["filieres"], db_counts["metiers"], db_counts["etablissements"],
    )
    return extraction
