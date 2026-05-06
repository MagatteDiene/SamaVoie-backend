from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Niveau(Base):
    __tablename__ = "niveaux"

    id: Mapped[int] = mapped_column(primary_key=True)
    designation: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
