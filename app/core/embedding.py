"""
Singleton BGE-M3 avec sélection automatique CUDA/CPU.

Règles d'architecture :
- Ce module est l'UNIQUE point d'accès au modèle d'embedding dans toute l'app.
- load_embedding_model() est appelé une seule fois depuis le lifespan de main.py.
- Les services (rag_engine, bge_indexer) importent get_embedding_model() ou encode_texts().
- Jamais de SentenceTransformer() directement en dehors de ce module.
"""

import logging
import threading
from typing import Optional

import torch
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger("samavoie.core.embedding")

_model: Optional[SentenceTransformer] = None
_device: str = "cpu"
_lock = threading.Lock()  # double-checked locking pour thread-safety à l'init


# ---------------------------------------------------------------------------
# Sélection du device
# ---------------------------------------------------------------------------

def _detect_device() -> str:
    """
    Retourne 'cuda' si un GPU compatible est détecté, sinon 'cpu'.
    Logue les infos VRAM pour faciliter le diagnostic (GTX 1650 Ti = 4 GB).
    """
    if not torch.cuda.is_available():
        logger.info("CUDA non disponible → device=cpu")
        return "cpu"

    gpu_name = torch.cuda.get_device_name(0)
    props = torch.cuda.get_device_properties(0)
    vram_total_gb = props.total_memory / 1024 ** 3
    vram_free_gb = torch.cuda.mem_get_info(0)[0] / 1024 ** 3

    logger.info(
        "GPU detecte : %s (compute %d.%d) | VRAM : %.1f GB total, %.1f GB libres → device=cuda",
        gpu_name,
        props.major,
        props.minor,
        vram_total_gb,
        vram_free_gb,
    )
    return "cuda"


# ---------------------------------------------------------------------------
# Chargement (appelé une seule fois depuis le lifespan)
# ---------------------------------------------------------------------------

def load_embedding_model() -> Optional[SentenceTransformer]:
    """
    Initialise le singleton BGE-M3.
    Stratégie de fallback : CUDA → CPU (si OOM) → None (si erreur critique).

    batch_size=32 est calibré pour GTX 1650 Ti (4 GB VRAM).
    BGE-M3 consomme ~600 MB en float32 + ~1 GB pour un batch de 32 chunks.
    """
    global _model, _device

    if _model is not None:
        return _model

    with _lock:
        if _model is not None:  # double-check après acquisition du verrou
            return _model

        device = _detect_device()

        try:
            logger.info("Chargement BGE-M3 (%s) sur %s...", settings.BGE_MODEL_NAME, device)
            _model = SentenceTransformer(
                settings.BGE_MODEL_NAME,
                device=device,
                trust_remote_code=True,
            )
            _device = device

        except torch.cuda.OutOfMemoryError:
            # VRAM insuffisante → fallback CPU automatique
            logger.warning(
                "CUDA OutOfMemoryError lors du chargement de BGE-M3 → fallback sur cpu"
            )
            torch.cuda.empty_cache()
            device = "cpu"
            _model = SentenceTransformer(
                settings.BGE_MODEL_NAME,
                device=device,
                trust_remote_code=True,
            )
            _device = device

        except Exception as exc:
            logger.error("Impossible de charger BGE-M3 : %s", exc)
            return None

        # Warm-up : première inférence pour initialiser les kernels CUDA
        # (évite la latence sur la première vraie requête)
        try:
            _model.encode(["init"], normalize_embeddings=True)
            if _device == "cuda":
                vram_used_gb = torch.cuda.memory_allocated(0) / 1024 ** 3
                logger.info(
                    "BGE-M3 pret sur %s | VRAM utilisee : %.2f GB",
                    _device,
                    vram_used_gb,
                )
            else:
                logger.info("BGE-M3 pret sur cpu")
        except Exception as exc:
            logger.warning("Warm-up BGE-M3 echoue (non bloquant) : %s", exc)

        return _model


def unload_embedding_model() -> None:
    """Libère le modèle et vide le cache CUDA (appelé au shutdown du lifespan)."""
    global _model, _device

    if _model is None:
        return

    del _model
    _model = None

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("Cache CUDA libere.")

    _device = "cpu"
    logger.info("BGE-M3 dechargé.")


# ---------------------------------------------------------------------------
# Accès au singleton (utilisé par rag_engine, bge_indexer…)
# ---------------------------------------------------------------------------

def get_embedding_model() -> SentenceTransformer:
    """
    Retourne l'instance singleton BGE-M3.
    Lève RuntimeError si appelé avant load_embedding_model().
    """
    if _model is None:
        raise RuntimeError(
            "BGE-M3 n'est pas initialisé. "
            "Vérifiez que le lifespan FastAPI s'est exécuté correctement."
        )
    return _model


def encode_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Encode une liste de textes en vecteurs normalisés (cosine-ready).

    batch_size=32 : calibré pour GTX 1650 Ti (4 GB VRAM).
    Réduire à 16 si d'autres processus GPU tournent en parallèle.
    """
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Introspection (exposé via /health)
# ---------------------------------------------------------------------------

def get_device_info() -> dict:
    """Retourne les infos sur le device actif — utilisé par le health check."""
    if _model is None:
        return {"status": "not_loaded", "device": "unknown"}

    info: dict = {
        "status": "loaded",
        "model": settings.BGE_MODEL_NAME,
        "device": _device,
    }

    if _device == "cuda" and torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["compute_capability"] = f"{props.major}.{props.minor}"
        info["vram_used_gb"] = round(torch.cuda.memory_allocated(0) / 1024 ** 3, 2)
        info["vram_total_gb"] = round(props.total_memory / 1024 ** 3, 2)

    return info
