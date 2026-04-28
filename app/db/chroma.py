from typing import Optional
import chromadb
from chromadb.api import ClientAPI
from app.config import settings

_client: Optional[ClientAPI] = None


def get_chroma_client() -> ClientAPI:
    """Singleton : un seul PersistentClient par processus pour éviter les lock conflicts."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
    return _client


def get_collection(name: str = "orientation_senegal") -> chromadb.Collection:
    """Récupère ou crée la collection ChromaDB (cosine similarity)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
