from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .db import AsyncSessionLocal


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an asynchronous SQLModel / SQLAlchemy Session."""
    async with AsyncSessionLocal() as session:
        yield session


# Alias for backward-compatibility
get_db = get_async_db
