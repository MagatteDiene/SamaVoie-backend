"""
Ingestion batch récursive — data/raw/ → data/processed/

Usage (depuis la racine du projet, .venv activé) :
    python -m scripts.test_ingestion_recursive

Le script parcourt data/raw/ récursivement, ingère chaque PDF trouvé via
run_pipeline(), puis déplace le fichier vers data/processed/ en conservant
l'arborescence de sous-dossiers. Les fichiers échoués restent dans data/raw/
pour permettre une reprise manuelle.
"""

import asyncio
import logging
import logging.config
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Résolution de la racine du projet — fonctionne que le script soit lancé via
# `python scripts/...` ou `python -m scripts....`
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Logging — même format que le reste de l'appli
# ---------------------------------------------------------------------------
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "transformers": {"level": "WARNING", "propagate": True},
            "sentence_transformers": {"level": "WARNING", "propagate": True},
            "chromadb": {"level": "WARNING", "propagate": True},
        },
    }
)
logger = logging.getLogger("samavoie.batch")


def _move_to_processed(src: Path) -> Path:
    """
    Déplace src (sous data/raw/) vers data/processed/ en conservant la
    sous-arborescence relative. Crée les dossiers destination si nécessaire.
    Retourne le chemin de destination.
    """
    rel = src.relative_to(RAW_DIR)
    dst = PROCESSED_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return dst


async def ingest_all() -> None:
    # --- Initialisation des ressources partagées ---
    from app.core.embedding import load_embedding_model, get_device_info
    from app.db.chroma import get_chroma_client
    from app.ingestion.pipeline import run_pipeline

    logger.info("Chargement BGE-M3…")
    model = load_embedding_model()
    if model is None:
        logger.warning("BGE-M3 non disponible — les embeddings ne seront pas indexés.")
    else:
        info = get_device_info()
        logger.info("BGE-M3 actif : device=%s | %s", info["device"], info.get("gpu_name", ""))

    try:
        get_chroma_client()
        logger.info("ChromaDB connecté.")
    except Exception as exc:
        logger.error("ChromaDB indisponible : %s — abandon.", exc)
        return

    # --- Découverte des PDFs ---
    pdfs = sorted(RAW_DIR.rglob("*.pdf"))
    if not pdfs:
        logger.info("Aucun PDF trouvé dans %s", RAW_DIR)
        return

    logger.info("=== %d PDF(s) trouvé(s) dans %s ===", len(pdfs), RAW_DIR)

    success_count = 0
    failure_count = 0

    for pdf_path in pdfs:
        rel = pdf_path.relative_to(RAW_DIR)
        logger.info("--- Début ingestion : %s ---", rel)
        try:
            result = await run_pipeline(pdf_path)

            dst = _move_to_processed(pdf_path)
            logger.info(
                "Succès ingestion pour %s, déplacé vers %s "
                "| filières=%d | métiers=%d | établissements=%d | chunks=%d",
                rel,
                dst.relative_to(PROJECT_ROOT),
                len(result.filieres),
                len(result.metiers),
                len(result.etablissements),
                len(result.chunks_texte),
            )
            success_count += 1

        except Exception as exc:
            logger.error("Échec ingestion pour %s : %s — fichier laissé dans data/raw/", rel, exc)
            failure_count += 1

    logger.info(
        "=== Batch terminé : %d succès, %d échec(s) ===",
        success_count,
        failure_count,
    )


if __name__ == "__main__":
    asyncio.run(ingest_all())
