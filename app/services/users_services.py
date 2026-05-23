from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.users import UserCreate


def _user_select():
    """Base select with eager-loaded relationships to prevent N+1 queries.

    Add ``.options(selectinload(...))`` here when User gains relationships.
    """
    return select(User)


def get_users(db: Session) -> Sequence[User]:
    return db.scalars(_user_select()).all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.scalars(_user_select().where(User.id == user_id)).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        hashed_pass=user_in.password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
