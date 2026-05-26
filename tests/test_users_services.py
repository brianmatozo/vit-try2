import pydantic
import pytest
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.users import UserCreate
from app.services.users_services import create_user, delete_user, get_user, get_users


class TestGetUsers:
    def test_empty_returns_empty_list(self, db_session: Session):
        result = get_users(db_session)
        assert result == []

    def test_returns_all_users(self, db_session: Session):
        u1 = User(username="alice", hashed_pass="h1")
        u2 = User(username="bob", hashed_pass="h2")
        db_session.add_all([u1, u2])
        db_session.commit()

        result = get_users(db_session)

        assert len(result) == 2
        assert result[0].username == "alice"
        assert result[1].username == "bob"


class TestGetUser:
    def test_existing_user_returns_user(self, db_session: Session):
        user = User(username="alice", hashed_pass="h1")
        db_session.add(user)
        db_session.commit()

        result = get_user(db_session, user.id)

        assert result is not None
        assert result.username == "alice"

    def test_nonexistent_user_returns_none(self, db_session: Session):
        result = get_user(db_session, 999)
        assert result is None

    def test_zero_id_returns_none(self, db_session: Session):
        result = get_user(db_session, 0)
        assert result is None

    def test_negative_id_returns_none(self, db_session: Session):
        result = get_user(db_session, -1)
        assert result is None


class TestCreateUser:
    def test_valid_input_creates_and_returns_user(self, db_session: Session):
        user_in = UserCreate(username="alice", password="secure123")

        result = create_user(db_session, user_in)

        assert result.id is not None
        assert result.username == "alice"
        assert result.hashed_pass == "secure123"

        persisted = db_session.get(User, result.id)
        assert persisted is not None
        assert persisted.username == "alice"

    def test_duplicate_username_does_not_raise_error(self, db_session: Session):
        create_user(db_session, UserCreate(username="alice", password="secure123"))
        # No unique constraint on username in the model, so this should succeed.
        result = create_user(
            db_session, UserCreate(username="alice", password="secure456")
        )
        assert result.id is not None

    def test_empty_username_fails_validation(self, db_session: Session):
        with pytest.raises(pydantic.ValidationError, match="username"):
            UserCreate(username="", password="secure123")

    def test_empty_password_fails_validation(self, db_session: Session):
        with pytest.raises(pydantic.ValidationError, match="password"):
            UserCreate(username="alice", password="")

    def test_max_boundary_strings_succeed(self, db_session: Session):
        max_name = "a" * 50
        max_pass = "b" * 128
        result = create_user(
            db_session, UserCreate(username=max_name, password=max_pass)
        )
        assert result.username == max_name
        assert result.hashed_pass == max_pass


class TestDeleteUser:
    def test_existing_user_is_deleted(self, db_session: Session):
        user = User(username="alice", hashed_pass="h1")
        db_session.add(user)
        db_session.commit()

        delete_user(db_session, user)

        assert db_session.get(User, user.id) is None

    def test_deleting_already_deleted_user_is_noop(self, db_session: Session):
        user = User(username="alice", hashed_pass="h1")
        db_session.add(user)
        db_session.commit()
        uid = user.id

        delete_user(db_session, user)
        assert db_session.get(User, uid) is None

        # Second delete on the same (now-expired) object is a no-op.
        delete_user(db_session, user)

    def test_nonexistent_user_raises(self, db_session: Session):
        phantom = User(id=999, username="ghost", hashed_pass="x")
        with pytest.raises(Exception):
            delete_user(db_session, phantom)
