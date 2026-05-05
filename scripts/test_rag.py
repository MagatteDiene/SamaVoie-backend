"""
Diagnostic RAG — SamaVoie / Kali

Teste le pipeline RAG complet en affichant :
  - Les chunks récupérés avec leurs scores de similarité
  - Le temps de chaque étape (embedding, retrieval, génération)
  - La réponse finale de Kali

Usage :
    python -m scripts.test_rag
    python -m scripts.test_rag "Quelles filières existent après un Bac S ?"
    python -m scripts.test_rag --top-k 8 "Quels sont les salaires en informatique ?"
"""

import asyncio
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Questions de test par défaut si aucune n'est fournie en argument
_DEFAULT_QUESTIONS = [
    "Quelles sont les filières disponibles après un Bac S au Sénégal ?",
    "Quels sont les débouchés de la filière informatique ?",
    "Quel est le salaire moyen d'un ingénieur au Sénégal ?",
]

SEP = "─" * 70


def _parse_args():
    args = sys.argv[1:]
    top_k = 5
    questions = []

    i = 0
    while i < len(args):
        if args[i] in ("--top-k", "-k") and i + 1 < len(args):
            top_k = int(args[i + 1])
            i += 2
        else:
            questions.append(args[i])
            i += 1

    return questions or _DEFAULT_QUESTIONS, top_k


async def _test_question(question: str, top_k: int) -> None:
    from app.core.embedding import encode_texts, load_embedding_model
    from app.db.chroma import get_collection

    print(f"\n{SEP}")
    print(f"  QUESTION : {question}")
    print(SEP)

    # ── Étape 1 : Embedding ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    query_vector = encode_texts([question])[0]
    t_embed = time.perf_counter() - t0
    print(f"[1] Embedding       : {t_embed*1000:.1f} ms")

    # ── Étape 2 : Retrieval ChromaDB ─────────────────────────────────────────
    t0 = time.perf_counter()
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    t_retrieval = time.perf_counter() - t0

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]   # distance cosine [0, 2] — plus petit = plus proche

    print(f"[2] Retrieval       : {t_retrieval*1000:.1f} ms  ({len(chunks)} chunks)")
    print()

    if not chunks:
        print("  ⚠ Aucun chunk trouvé dans ChromaDB — corpus vide ?")
        return

    # Affichage des chunks récupérés
    print("  CHUNKS RÉCUPÉRÉS :")
    for i, (chunk, meta, dist) in enumerate(zip(chunks, metadatas, distances), 1):
        score = 1 - dist / 2          # conversion distance cosine → similarité [0, 1]
        source = meta.get("source", "?")
        preview = chunk[:200].replace("\n", " ")
        print(f"\n  [{i}] Score : {score:.3f} | Source : {source}")
        print(f"      {preview}{'…' if len(chunk) > 200 else ''}")

    # ── Étape 3 : Génération Ollama ──────────────────────────────────────────
    print(f"\n{SEP}")
    print("  GÉNÉRATION (Kali)…")

    import httpx
    from app.core.rag_engine import _OLLAMA_BASE_URL, _OLLAMA_MODEL, _OLLAMA_TIMEOUT, _SYSTEM_PROMPT

    context = "\n\n---\n\n".join(chunks)
    user_message = f"Extraits de documents :\n{context}\n\nQuestion : {question}"

    payload = {
        "model": _OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
        response = await client.post(f"{_OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()
    t_gen = time.perf_counter() - t0

    answer = response.json()["message"]["content"]

    print(f"[3] Génération      : {t_gen:.1f} s")
    print(f"    Tokens générés  : ~{len(answer.split())} mots")
    print()
    print("  RÉPONSE DE KALI :")
    print()
    for line in answer.strip().splitlines():
        print(f"  {line}")

    # ── Récapitulatif ────────────────────────────────────────────────────────
    total = t_embed + t_retrieval + t_gen
    sources = list({m.get("source", "?") for m in metadatas})
    print()
    print(SEP)
    print(f"  TEMPS TOTAL : {total:.2f} s  "
          f"(embed {t_embed*1000:.0f}ms + retrieval {t_retrieval*1000:.0f}ms + gen {t_gen:.1f}s)")
    print(f"  SOURCES     : {', '.join(sources)}")
    print(SEP)


async def main() -> None:
    questions, top_k = _parse_args()

    # Initialisation BGE-M3 (une seule fois pour toutes les questions)
    from app.core.embedding import load_embedding_model
    print("Chargement BGE-M3…")
    load_embedding_model()
    print(f"top_k={top_k} | modèle LLM={__import__('app.core.rag_engine', fromlist=['_OLLAMA_MODEL'])._OLLAMA_MODEL}")

    for q in questions:
        await _test_question(q, top_k)

    print()


if __name__ == "__main__":
    asyncio.run(main())
