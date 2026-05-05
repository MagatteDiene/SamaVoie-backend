import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.core.rag_engine import query
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger("samavoie.api.chat")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint RAG principal.
    Reçoit une question, interroge ChromaDB, génère une réponse via Ollama.
    """
    try:
        answer, sources = await query(request.message)
    except Exception as exc:
        logger.error("Erreur RAG pour '%s' : %s", request.message, exc)
        raise HTTPException(status_code=503, detail="Le moteur RAG est temporairement indisponible.")

    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Chat | session=%s | sources=%s | question=%s",
        session_id, sources, request.message[:60],
    )

    return ChatResponse(answer=answer, sources=sources, session_id=session_id)
