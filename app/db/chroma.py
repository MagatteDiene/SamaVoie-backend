import chromadb
from app.config import settings

def get_chroma_client():
    """Initialise et retourne le client ChromaDB persistant."""
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)

def get_collection(name: str = "orientation_senegal"):
    """Récupère ou crée une collection dans ChromaDB."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"} # Utilisation de la similarité cosinus par défaut
    )
