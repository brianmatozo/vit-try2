from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserResponse
from app.services import users_services as service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users",
    description="Returns a list of all registered users in the system.",
    response_description="A list of user objects.",
    operation_id="listUsers",
)
def list_users(db: Session = Depends(get_db)) -> Sequence[User]:
    """Retrieve every registered user."""
    return service.get_users(db)


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
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    """Retrieve one user by primary key."""
    user = service.get_user(db, user_id)
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
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    """Register a new user."""
    return service.create_user(db, user_in)


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
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one user by primary key."""
    user = service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    service.delete_user(db, user)
