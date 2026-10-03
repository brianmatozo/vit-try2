from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.dependencies import get_async_db
from server.models.users import User
from server.schemas.users import UserCreate, UserResponse
from server.services import users_services as service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users",
    description="Returns a list of all registered users in the system.",
    response_description="A list of user objects.",
    operation_id="listUsers",
)
async def list_users(db: AsyncSession = Depends(get_async_db)) -> Sequence[User]:
    """Retrieve every registered user."""
    return await service.get_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID",
    description="Fetch a single user by their unique numeric identifier.",
    response_description="The requested user object.",
    operation_id="getUser",
    responses={
        404: {"description": "No user found with the given ID."},
    },
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)) -> User:
    """Retrieve one user by primary key."""
    user = await service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Register a new user account with a username and password.",
    response_description="The newly created user object.",
    operation_id="createUser",
)
async def create_user(
    user_in: UserCreate, db: AsyncSession = Depends(get_async_db)
) -> User:
    """Register a new user."""
    return await service.create_user(db, user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="Permanently remove a user account by ID.",
    response_description="No content — deletion succeeded.",
    operation_id="deleteUser",
    responses={
        404: {"description": "No user found with the given ID."},
    },
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete one user by primary key."""
    user = await service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await service.delete_user(db, user)
