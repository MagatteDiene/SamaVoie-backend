from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = Field(..., description="Clé API Google Gemini 1.5 Pro")
    OPENAI_API_KEY: Optional[str] = Field(None, description="Clé API OpenAI (si LLM_PROVIDER=openai)")
    MISTRAL_API_KEY: Optional[str] = Field(None, description="Clé API Mistral (si LLM_PROVIDER=mistral)")

    # Security
    JWT_SECRET_KEY: str = Field(..., description="Clé secrète JWT — générer avec: openssl rand -hex 32")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours (MVP) — réduire à 30 min en prod

    # Databases
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://user:pass@localhost:5432/orientation_db",
        description="URL de connexion PostgreSQL (asyncpg pour async)",
    )
    CHROMA_PERSIST_PATH: str = Field("./chroma_db", description="Chemin de persistance ChromaDB")

    # RAG
    BGE_MODEL_NAME: str = Field("BAAI/bge-m3", description="Modèle local pour les embeddings")
    LLM_PROVIDER: str = Field("gemini", description="gemini | openai | mistral")
    RAG_TOP_K: int = Field(5, description="Nombre de chunks récupérés par ChromaDB")

    # CORS — liste d'origines autorisées (séparées par des virgules dans .env)
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Origines CORS autorisées",
    )

    # Project
    PROJECT_NAME: str = "SamaVoie Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        allowed = {"gemini", "openai", "mistral", "llama"}
        if v not in allowed:
            raise ValueError(f"LLM_PROVIDER doit être l'un de {allowed}")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
