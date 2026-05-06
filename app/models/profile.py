from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base
from app.models.associations import profile_interets

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.niveau import Niveau
    from app.models.serie import Serie
    from app.models.interet import Interet


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_profiles_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ville: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    niveau_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("niveaux.id", ondelete="SET NULL"), nullable=True
    )
    serie_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("series.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
    niveau: Mapped[Optional["Niveau"]] = relationship("Niveau", lazy="raise")
    serie: Mapped[Optional["Serie"]] = relationship("Serie", lazy="raise")
    interets: Mapped[List["Interet"]] = relationship(
        "Interet", secondary=profile_interets, lazy="raise"
    )
