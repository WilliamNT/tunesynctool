from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField

class User(SQLModel, table=True):
    """
    Represents a user model.
    """

    __tablename__ = "users"

    id: int = SQLField(default=None, primary_key=True)
    username: str = SQLField(unique=True, index=True, max_length=255)
    password_hash: str = SQLField(max_length=255)
    is_admin: bool = SQLField(default=False)

class UserCreate(BaseModel):
    """
    Represents a user creation DTO.
    """

    username: str = Field(max_length=255, min_length=3, description="Username must be unique and be at least 3 characters long.")
    password: str = Field(max_length=255, min_length=8, description="Password must be at least 8 characters long.")

class UserRead(BaseModel):
    """
    Represents a user response DTO.
    """

    id: int = Field(description="User ID")
    username: str = Field(max_length=255, description="Username")
    is_admin: bool = Field(default=False, description="Whether the user is an admin")

class UserLogin(UserCreate):
    """
    Represents a user login DTO.

    Currently an alias for UserCreate.
    """

    pass

class UserLookupByIdParams(BaseModel):
    id: int = Field(description="User ID")