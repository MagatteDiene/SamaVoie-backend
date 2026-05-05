import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rag_engine import query
from app.db.postgres import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger("samavoie.api.chat")

# Auth optionnelle — le chat fonctionne aussi en mode anonyme
_optional_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def _get_optional_user(
    token: Optional[str] = Depends(_optional_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        if not email:
            return None
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user if (user and user.is_active) else None
    except JWTError:
        return None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    """
    Endpoint RAG principal.

    - Anonyme : répond sans historique ni personnalisation.
    - Authentifié : charge l'historique de session (5 derniers échanges),
      personnalise le system prompt avec le profil utilisateur,
      persiste la nouvelle paire question/réponse en base.
    """
    session_id = request.session_id
    conversation: Optional[Conversation] = None
    history: list[dict] = []
    user_context: Optional[dict] = None

    if current_user:
        # Récupère ou crée la conversation
        if session_id:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.session_id == session_id,
                    Conversation.user_id == current_user.id,
                )
            )
            conversation = result.scalar_one_or_none()

        if conversation is None:
            session_id = session_id or str(uuid.uuid4())
            conversation = Conversation(
                user_id=current_user.id,
                session_id=session_id,
                messages=[],
            )
            db.add(conversation)
            await db.flush()

        # 5 échanges = 10 messages
        history = list(conversation.messages[-10:])

        user_context = {
            "prenom": current_user.prenom,
            "nom":    current_user.nom,
            "profile": current_user.profile or {},
        }

    session_id = session_id or str(uuid.uuid4())

    try:
        answer, sources = await query(
            request.message,
            history=history or None,
            user_context=user_context,
        )
    except Exception as exc:
        logger.error("Erreur RAG pour '%s' : %s", request.message, exc)
        raise HTTPException(status_code=503, detail="Le moteur RAG est temporairement indisponible.")

    # Persiste l'échange (messages bruts — sans contexte RAG injecté)
    if conversation is not None:
        conversation.messages = conversation.messages + [
            {"role": "user",      "content": request.message},
            {"role": "assistant", "content": answer},
        ]
        await db.commit()

    logger.info(
        "Chat | session=%s | user=%s | sources=%s | question=%s",
        session_id,
        current_user.email if current_user else "anonymous",
        sources,
        request.message[:60],
    )

    return ChatResponse(answer=answer, sources=sources, session_id=session_id)
