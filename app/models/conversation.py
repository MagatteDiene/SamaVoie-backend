from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.postgres import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # Stockage des messages (format : {"role": "user/assistant", "content": str})
    messages: Mapped[list] = mapped_column(JSON, default=list)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relation
    user: Mapped["User"] = relationship("User", back_populates="conversations")
