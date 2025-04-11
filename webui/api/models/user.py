from pydantic import BaseModel
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    """
    Represents a user model.
    """

    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=255)    
    password_hash: str = Field(max_length=255)
    is_admin: bool = Field(default=False)

class UserCreate(BaseModel):
    """
    Represents a user creation DTO.
    """

    username: str = Field(unique=True, index=True, max_length=255, min_length=3, description="Username must be unique and at least 3 characters long.")    
    password: str = Field(max_length=255, min_length=8, description="Password must be at least 8 characters long.")

class UserRead(BaseModel):
    """
    Represents a user response DTO.
    """

    id: int = Field(nullable=False, description="User ID")
    username: str = Field(max_length=255, description="Username")
    is_admin: bool = Field(default=False, description="Whether the user is an admin")

class UserLogin(UserCreate):
    """
    Represents a user login DTO.

    Currently an alias for UserCreate.
    """

    pass