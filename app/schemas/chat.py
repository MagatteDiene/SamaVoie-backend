from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    session_id: Optional[str] = Field(None, description="ID de session existante")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: int
    session_id: str
    messages: List[MessageRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationSummary(BaseModel):
    """Vue allégée pour lister les sessions sans charger tous les messages."""
    id: int
    session_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
