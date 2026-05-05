import logging

import httpx

from app.config import settings
from app.core.embedding import encode_texts
from app.db.chroma import get_collection

logger = logging.getLogger("samavoie.core.rag_engine")

_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_MODEL    = "qwen2.5:3b"
_OLLAMA_TIMEOUT  = 120.0  # 3b model — beaucoup plus rapide

_SYSTEM_PROMPT = """\
Tu es Kali, l'intelligence artificielle intégrée à la plateforme SamaVoie, spécialisée en orientation académique et professionnelle dans le système sénégalais.
Tu réponds en français, de façon claire et structurée, en t'appuyant UNIQUEMENT sur les extraits de documents fournis.
Si l'information n'est pas dans les extraits, dis-le honnêtement sans inventer.\
"""


async def query(question: str, top_k: int | None = None) -> tuple[str, list[str]]:
    """
    Pipeline RAG complet :
      1. Encode la question avec BGE-M3
      2. Récupère les top_k chunks les plus proches dans ChromaDB
      3. Envoie la question + contexte à Ollama (gemma4:e4b)
      4. Retourne (réponse, liste des sources)
    """
    k = top_k or settings.RAG_TOP_K

    # --- Étape 1 : encodage de la question ---
    query_vector = encode_texts([question])[0]

    # --- Étape 2 : recherche sémantique ChromaDB ---
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        include=["documents", "metadatas"],
    )

    chunks: list[str] = results["documents"][0]
    sources: list[str] = list({
        m.get("source", "inconnu") for m in results["metadatas"][0]
    })

    if not chunks:
        return "Je n'ai pas trouvé d'informations pertinentes dans ma base de connaissances.", []

    context = "\n\n---\n\n".join(chunks)

    logger.debug("RAG : %d chunks récupérés depuis %s", len(chunks), sources)

    # --- Étape 3 : génération avec Ollama ---
    user_message = (
        f"Extraits de documents :\n{context}\n\n"
        f"Question : {question}"
    )

    payload = {
        "model": _OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
        },
    }

    async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
        response = await client.post(f"{_OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()

    answer: str = response.json()["message"]["content"]
    return answer, sources
