from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Database model representing a registered user."""

    __tablename__ = "users"

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="Unique user identifier",
    )
    username: str = Field(
        index=True,
        description="Unique username chosen by the user",
    )
    hashed_pass: str = Field(
        description="BCrypt-hashed password",
    )
