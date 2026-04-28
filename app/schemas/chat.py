from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000, description="Question de l'utilisateur")
    session_id: Optional[str] = Field(None, description="ID de session existante (reprise de contexte)")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class MessageSchema(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ConversationRead(BaseModel):
    id: int
    session_id: str
    messages: List[MessageSchema]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
