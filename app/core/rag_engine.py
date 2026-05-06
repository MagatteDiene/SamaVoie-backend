import logging

import httpx

from app.config import settings
from app.core.embedding import encode_texts
from app.db.chroma import get_collection

logger = logging.getLogger("samavoie.core.rag_engine")

_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_MODEL    = "qwen2.5:3b"
_OLLAMA_TIMEOUT  = 120.0

_SYSTEM_PROMPT_BASE = """\
Tu es Kali, l'intelligence artificielle intégrée à la plateforme SamaVoie, spécialisée en orientation académique et professionnelle dans le système sénégalais.
Tu réponds en français, de façon claire et structurée, en t'appuyant UNIQUEMENT sur les extraits de documents fournis.
Si l'information n'est pas dans les extraits, dis-le honnêtement sans inventer.\
"""

_HISTORY_LIMIT = 10  # 5 échanges = 10 messages


def _build_system_prompt(user_context: dict | None) -> str:
    """Construit le system prompt en injectant le profil utilisateur si disponible.

    user_context attendu (tous les champs optionnels) :
        { prenom, nom, niveau, serie, interets: list[str] }
    """
    if not user_context:
        return _SYSTEM_PROMPT_BASE

    lines = [_SYSTEM_PROMPT_BASE, ""]

    prenom   = (user_context.get("prenom") or "").strip()
    niveau   = (user_context.get("niveau") or "").strip()
    serie    = (user_context.get("serie")  or "").strip()
    interets: list = user_context.get("interets") or []

    if prenom:
        lines.append(f"Tu parles à {prenom}.")

    if niveau or serie:
        ctx = f"Niveau scolaire : {niveau}" if niveau else ""
        if serie:
            ctx = (ctx + f", Série : {serie}") if ctx else f"Série : {serie}"
        lines.append(ctx)

    if interets:
        lines.append(f"Centres d'intérêt : {', '.join(interets)}.")

    if prenom or niveau or interets:
        lines.append("Adapte tes réponses à son profil.")

    return "\n".join(lines)


async def query(
    question: str,
    top_k: int | None = None,
    history: list[dict] | None = None,
    user_context: dict | None = None,
) -> tuple[str, list[str]]:
    """
    Pipeline RAG complet :
      1. Encode la question avec BGE-M3
      2. Récupère les top_k chunks les plus proches dans ChromaDB
      3. Envoie question + contexte + historique à Ollama
      4. Retourne (réponse, liste des sources)

    Args:
        history: derniers messages [{role, content}] — le RAG injecte le contexte
                 uniquement dans le message courant, pas dans l'historique.
        user_context: {prenom, nom, profile: {niveau, serie, interets}} pour
                      personnaliser le system prompt.
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

    # --- Étape 3 : construction des messages ---
    system_prompt = _build_system_prompt(user_context)

    # Message courant : la question enrichie du contexte RAG
    current_user_message = f"Extraits de documents :\n{context}\n\nQuestion : {question}"

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Historique des échanges précédents (messages bruts, sans contexte RAG)
    if history:
        messages.extend(history[-_HISTORY_LIMIT:])

    messages.append({"role": "user", "content": current_user_message})

    payload = {
        "model": _OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3},
    }

    async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
        response = await client.post(f"{_OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()

    answer: str = response.json()["message"]["content"]
    return answer, sources
