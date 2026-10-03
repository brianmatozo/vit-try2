from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from server.core.config import settings


def get_async_database_url(url: str) -> str:
    """Translate database URL to its asynchronous driver counterpart."""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if (
        url.startswith("postgresql://")
        and "+psycopg" not in url
        and "+asyncpg" not in url
    ):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


async_database_url = get_async_database_url(settings.database_url)
async_connect_args: dict[str, Any] = {}
if "sqlite" in async_database_url:
    async_connect_args["check_same_thread"] = False

async_engine = create_async_engine(
    async_database_url,
    connect_args=async_connect_args,
)

if "sqlite" in async_database_url:

    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_async_sqlite_pragmas(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = SQLModel
