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

class UserCreate(SQLModel):
    """
    Represents a user creation DTO.
    """

    username: str = Field(unique=True, index=True, max_length=255)    
    password: str = Field(max_length=255)

class UserRead(SQLModel):
    """
    Represents a user response DTO.
    """

    id: int
    username: str
    is_admin: bool