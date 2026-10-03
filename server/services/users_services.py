from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.models.users import User
from server.schemas.users import UserCreate


async def get_users(db: AsyncSession) -> Sequence[User]:
    result = await db.scalars(select(User))
    return result.all()


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.scalars(select(User).where(User.id == user_id))
    return result.first()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        hashed_pass=user_in.password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
