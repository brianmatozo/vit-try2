from collections.abc import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from .db import AsyncSessionLocal, SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency providing a synchronous SQLModel Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an asynchronous SQLModel / SQLAlchemy Session."""
    async with AsyncSessionLocal() as session:
        yield session
