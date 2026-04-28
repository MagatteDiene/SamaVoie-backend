from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, JSON
from app.db.postgres import Base
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.conversation import Conversation

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Profil stocké en JSON pour la flexibilité (niveau, série, intérêts)
    profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relations
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
