from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.profile import Profile


class User(Base):
    """Données d'authentification uniquement. Les données de profil sont dans Profile."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
