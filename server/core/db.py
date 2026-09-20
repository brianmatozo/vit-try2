from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from server.core.config import settings


def get_sync_database_url(url: str) -> str:
    """Normalize database URL for synchronous SQLAlchemy engine."""
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if (
        url.startswith("postgresql://")
        and "+psycopg" not in url
        and "+asyncpg" not in url
    ):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


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


sync_database_url = get_sync_database_url(settings.database_url)
sync_connect_args: dict[str, Any] = {}
if "sqlite" in sync_database_url:
    sync_connect_args["check_same_thread"] = False

engine = create_engine(
    sync_database_url,
    connect_args=sync_connect_args,
)

if "sqlite" in sync_database_url:

    @event.listens_for(engine, "connect")
    def _set_sync_sqlite_pragmas(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

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
