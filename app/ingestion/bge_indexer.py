import logging
from typing import List

from app.core.embedding import encode_texts
from app.db.chroma import get_collection

logger = logging.getLogger("samavoie.ingestion.bge_indexer")


def index_chunks(chunks: List[str], source: str, batch_size: int = 32) -> int:
    """
    Encode les chunks via BGE-M3 et les indexe dans ChromaDB.

    Utilise upsert pour que la ré-indexation d'un même PDF soit idempotente.
    Retourne le nombre de chunks indexés.
    """
    if not chunks:
        logger.warning("index_chunks appelé avec une liste vide (source=%s)", source)
        return 0

    collection = get_collection()
    ids = [f"{source}::{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
    total = 0

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        batch_chunks = chunks[start:end]
        embeddings = encode_texts(batch_chunks, batch_size=batch_size)

        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings,
            documents=batch_chunks,
            metadatas=metadatas[start:end],
        )
        total += len(batch_chunks)
        logger.info("ChromaDB : %d/%d chunks indexés (source=%s)", total, len(chunks), source)

    return total
