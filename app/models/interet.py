from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Interet(Base):
    __tablename__ = "interets"

    id: Mapped[int] = mapped_column(primary_key=True)
    designation: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
