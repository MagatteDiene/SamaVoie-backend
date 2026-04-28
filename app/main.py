from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Plateforme d'Orientation Académique au Sénégal (RAG + LLM)"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# TODO: Inclure les routers dans les prochaines phases
# from app.api import auth, chat, filieres, metiers, etablissements
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(chat.router, prefix="/chat", tags=["Chat & RAG"])
