from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import Session

import server.models  # noqa: F401
from server.core.db import Base
from server.core.dependencies import get_async_db, get_db
from server.main import app


@pytest.fixture
def test_db_path(tmp_path):
    """Temporary SQLite database file isolated per test."""
    db_file = tmp_path / "test.db"
    return str(db_file)


@pytest.fixture
def sync_engine(test_db_path: str):
    engine: Engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def async_engine(test_db_path: str, sync_engine):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture
def db_session(sync_engine: Engine):
    """Synchronous session fixture for testing SQLModel models directly."""
    session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=sync_engine, class_=Session
    )
    with session_factory() as session:
        yield session


@pytest.fixture
async def async_session(async_engine):
    """Asynchronous session fixture for testing async services."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def client(async_engine):
    """TestClient with database dependencies overridden for isolated SQLite tests."""
    async_session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_async_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_db] = override_get_async_db
    app.dependency_overrides[get_db] = override_get_async_db

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def noop_lifespan(_):
        yield

    app.router.lifespan_context = noop_lifespan
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()
