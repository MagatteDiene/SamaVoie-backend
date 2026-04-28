from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = Field(..., description="Clé API pour Google Gemini 1.5 Pro")
    OPENAI_API_KEY: Optional[str] = Field(None, description="Clé API OpenAI (si LLM_PROVIDER=openai)")
    
    # Security
    JWT_SECRET_KEY: str = Field(..., description="Clé secrète pour la génération des tokens JWT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 semaine
    
    # Databases
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://user:pass@localhost:5432/orientation_db",
        description="URL de connexion PostgreSQL (asyncpg)"
    )
    CHROMA_PERSIST_PATH: str = Field("./chroma_db", description="Chemin de persistance pour ChromaDB")
    
    # RAG Configuration
    BGE_MODEL_NAME: str = Field("BAAI/bge-m3", description="Modèle local pour les embeddings")
    LLM_PROVIDER: str = Field("gemma", description="Fournisseur LLM : gemma | gemini | openai | mistral")
    
    # Project Info
    PROJECT_NAME: str = "SamaVoie Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
