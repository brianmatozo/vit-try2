from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(
        description="Unique username for the user account",
        min_length=3,
        max_length=50,
        examples=["johndoe"],
    )


class UserCreate(UserBase):
    password: str = Field(
        description="Plain-text password (hashed before storage)",
        min_length=8,
        max_length=128,
        examples=["s3cur3P@ss!"],
    )


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        description="Unique identifier for the user",
        examples=[1],
    )
