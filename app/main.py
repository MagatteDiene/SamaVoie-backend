import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings

# ---------------------------------------------------------------------------
# Logging structuré — initialisé avant tout import applicatif
# ---------------------------------------------------------------------------
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if settings.DEBUG else "INFO",
    },
    "loggers": {
        "uvicorn": {"propagate": True},
        "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
        # Silence les loggers verbeux de torch/transformers en prod
        "transformers": {"level": "WARNING", "propagate": True},
        "sentence_transformers": {"level": "WARNING", "propagate": True},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("samavoie")


# ---------------------------------------------------------------------------
# Lifespan — chargement / libération des ressources coûteuses
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage SamaVoie Backend v%s", settings.VERSION)

    # --- BGE-M3 : délégué entièrement à core/embedding ---
    # Le singleton gère la détection CUDA, le fallback CPU et le warm-up.
    from app.core.embedding import load_embedding_model, get_device_info
    model = load_embedding_model()
    if model is None:
        logger.warning("BGE-M3 non disponible — les endpoints RAG seront dégradés.")
    else:
        info = get_device_info()
        logger.info("BGE-M3 actif : device=%s | %s", info["device"], info.get("gpu_name", ""))

    # --- ChromaDB : vérification de la connexion au démarrage ---
    try:
        from app.db.chroma import get_chroma_client
        get_chroma_client()
        logger.info("ChromaDB connecté : %s", settings.CHROMA_PERSIST_PATH)
    except Exception as exc:
        logger.error("ChromaDB indisponible au démarrage : %s", exc)

    yield  # l'application tourne

    # --- Shutdown : libération explicite du GPU ---
    from app.core.embedding import unload_embedding_model
    unload_embedding_model()
    logger.info("Arrêt propre du serveur.")


# ---------------------------------------------------------------------------
# Application FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Plateforme d'Orientation Académique au Sénégal (RAG + LLM)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Handlers d'exceptions — format standard {"success", "error", "message"}
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error | path=%s | %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Données de la requête invalides",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception | path=%s | %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Une erreur interne est survenue. Veuillez réessayer.",
        },
    )


# ---------------------------------------------------------------------------
# Routes de base
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {
        "success": True,
        "data": {"project": settings.PROJECT_NAME, "version": settings.VERSION},
        "message": "OK",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Retourne l'état de santé du serveur, y compris les infos GPU/device de BGE-M3.
    Utile pour vérifier que le modèle tourne bien sur CUDA en développement.
    """
    from app.core.embedding import get_device_info
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "embedding_model": get_device_info(),
        },
        "message": "OK",
    }


# ---------------------------------------------------------------------------
# Routers — décommentés progressivement par phase
# ---------------------------------------------------------------------------
# Phase 3 — Auth
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Phase 5 — Chat RAG
from app.api.chat import router as chat_router
app.include_router(chat_router, prefix="/chat", tags=["Chat & RAG"])

# Phase 4 — Référentiel CRUD
from app.api.filieres import router as filieres_router
from app.api.metiers import router as metiers_router
from app.api.etablissements import router as etablissements_router
app.include_router(filieres_router, prefix="/filieres", tags=["Filières"])
app.include_router(metiers_router, prefix="/metiers", tags=["Métiers"])
app.include_router(etablissements_router, prefix="/etablissements", tags=["Établissements"])

# Phase 5 — Historique & Admin
# from app.api.history import router as history_router
# from app.api.admin import router as admin_router
# app.include_router(history_router, prefix="/history", tags=["Historique"])
# app.include_router(admin_router, prefix="/admin", tags=["Administration"])
