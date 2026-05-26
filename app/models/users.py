from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    """Database model representing a registered user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="Unique user identifier"
    )
    username: Mapped[str] = mapped_column(
        String, index=True, comment="Unique username chosen by the user"
    )
    hashed_pass: Mapped[str] = mapped_column(String, comment="BCrypt-hashed password")
