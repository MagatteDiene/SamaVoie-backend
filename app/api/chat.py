import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.rag_engine import query
from app.db.postgres import get_db
from app.dependencies import _user_with_profile_options
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.profile import Profile
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger("samavoie.api.chat")

_optional_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
_HISTORY_LIMIT = 10  # 5 échanges = 10 messages


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
        result = await db.execute(
            select(User)
            .options(_user_with_profile_options())
            .where(User.email == email)
        )
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
    - Authentifié : charge l'historique de session, personnalise le prompt
      avec le profil utilisateur, persiste la paire question/réponse.
    """
    session_id = request.session_id
    conversation: Optional[Conversation] = None
    history: list[dict] = []
    user_context: Optional[dict] = None

    if current_user:
        if session_id:
            result = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(
                    Conversation.session_id == session_id,
                    Conversation.user_id == current_user.id,
                )
            )
            conversation = result.scalar_one_or_none()

        if conversation is None:
            session_id = session_id or str(uuid.uuid4())
            conversation = Conversation(user_id=current_user.id, session_id=session_id)
            db.add(conversation)
            await db.flush()

        past_messages = conversation.messages[-_HISTORY_LIMIT:]
        history = [{"role": m.role, "content": m.content} for m in past_messages]

        profile: Optional[Profile] = current_user.profile
        user_context = {
            "prenom":   current_user.prenom,
            "nom":      current_user.nom,
            "niveau":   profile.niveau.designation if profile and profile.niveau else "",
            "serie":    profile.serie.designation if profile and profile.serie else "",
            "interets": [i.designation for i in profile.interets] if profile else [],
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

    if conversation is not None:
        db.add(Message(conversation_id=conversation.id, role="user", content=request.message))
        db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()

    logger.info(
        "Chat | session=%s | user=%s | sources=%s | question=%.60s",
        session_id,
        current_user.email if current_user else "anonymous",
        sources,
        request.message,
    )

    return ChatResponse(answer=answer, sources=sources, session_id=session_id)
