from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] # Liens vers les documents ou chunks utilisés
    session_id: str

class MessageSchema(BaseModel):
    role: str # "user" ou "assistant"
    content: str

class ConversationRead(BaseModel):
    id: int
    session_id: str
    messages: List[MessageSchema]
    
    class Config:
        from_attributes = True
