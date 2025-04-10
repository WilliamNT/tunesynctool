from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models.user import UserCreate, User
from api.core.security import hash_password
from api.helpers.database import create
from api.core.database import get_session
from api.core.logging import logger

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate) -> User:
        """
        Creates a new user in the database and returns it afterwards.
        
        :param user: The user to create.
        :return: The created user.
        """

        if await self.is_username_taken(user.username):
            raise HTTPException(
                status_code=400,
                detail="Username already taken",
            )

        new_user = User(
            username=user.username,
            password_hash=hash_password(user.password),
            is_admin=False,
        )

        logger.info(f"Creating user {user.username}.")

        return await create(
            session=self.db,
            obj=new_user,
        )
    
    async def is_username_taken(self, username: str) -> bool:
        """
        Checks if a username is already taken.
        
        :param username: The username to check.
        :return: True if the username is taken, otherwise False.
        """
        
        result = await self.db.execute(
            select(User).where(User.username == username)
        )

        return result.scalar_one_or_none() is not None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username.
        
        :param username: The username of the user.
        :return: The user if found, otherwise None.
        """
        
        result = await self.db.execute(
            select(User).where(User.username == username)
        )

        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by ID.
        
        :param user_id: The ID of the user.
        :return: The user if found, otherwise None.
        """
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()
    
def get_user_service(db: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(db)