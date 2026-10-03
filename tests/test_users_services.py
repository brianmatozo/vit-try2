import pydantic
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.users import User
from server.schemas.users import UserCreate
from server.services.users_services import create_user, delete_user, get_user, get_users

pytestmark = pytest.mark.anyio


class TestGetUsers:
    async def test_empty_returns_empty_list(self, async_session: AsyncSession):
        result = await get_users(async_session)
        assert list(result) == []

    async def test_returns_all_users(self, async_session: AsyncSession):
        u1 = User(username="alice", hashed_pass="h1")
        u2 = User(username="bob", hashed_pass="h2")
        async_session.add_all([u1, u2])
        await async_session.commit()

        result = await get_users(async_session)

        assert len(result) == 2
        assert result[0].username == "alice"
        assert result[1].username == "bob"


class TestGetUser:
    async def test_existing_user_returns_user(self, async_session: AsyncSession):
        user = User(username="alice", hashed_pass="h1")
        async_session.add(user)
        await async_session.commit()
        assert user.id is not None

        result = await get_user(async_session, user.id)

        assert result is not None
        assert result.username == "alice"

    async def test_nonexistent_user_returns_none(self, async_session: AsyncSession):
        result = await get_user(async_session, 999)
        assert result is None

    async def test_zero_id_returns_none(self, async_session: AsyncSession):
        result = await get_user(async_session, 0)
        assert result is None

    async def test_negative_id_returns_none(self, async_session: AsyncSession):
        result = await get_user(async_session, -1)
        assert result is None


class TestCreateUser:
    async def test_valid_input_creates_and_returns_user(
        self, async_session: AsyncSession
    ):
        user_in = UserCreate(username="alice", password="secure123")

        result = await create_user(async_session, user_in)

        assert result.id is not None
        assert result.username == "alice"
        assert result.hashed_pass == "secure123"

        persisted = await async_session.get(User, result.id)
        assert persisted is not None
        assert persisted.username == "alice"

    async def test_duplicate_username_does_not_raise_error(
        self, async_session: AsyncSession
    ):
        await create_user(
            async_session, UserCreate(username="alice", password="secure123")
        )
        result = await create_user(
            async_session, UserCreate(username="alice", password="secure456")
        )
        assert result.id is not None

    def test_empty_username_fails_validation(self):
        with pytest.raises(pydantic.ValidationError, match="username"):
            UserCreate(username="", password="secure123")

    def test_empty_password_fails_validation(self):
        with pytest.raises(pydantic.ValidationError, match="password"):
            UserCreate(username="alice", password="")

    async def test_max_boundary_strings_succeed(self, async_session: AsyncSession):
        max_name = "a" * 50
        max_pass = "b" * 128
        result = await create_user(
            async_session, UserCreate(username=max_name, password=max_pass)
        )
        assert result.username == max_name
        assert result.hashed_pass == max_pass


class TestDeleteUser:
    async def test_existing_user_is_deleted(self, async_session: AsyncSession):
        user = User(username="alice", hashed_pass="h1")
        async_session.add(user)
        await async_session.commit()

        await delete_user(async_session, user)

        assert await async_session.get(User, user.id) is None

    async def test_nonexistent_user_raises(self, async_session: AsyncSession):
        phantom = User(id=999, username="ghost", hashed_pass="x")
        with pytest.raises(Exception):
            await delete_user(async_session, phantom)
