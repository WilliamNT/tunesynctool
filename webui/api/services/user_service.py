from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models.user import UserCreate, User, UserRead
from api.core.security import hash_password
from api.helpers.database import create
from api.core.database import get_session
from api.core.logging import logger
from api.core.config import config
from api.models.collection import Collection

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate) -> User:
        """
        Creates a new user in the database and returns it afterwards.
        
        :param user: The user to create.
        :return: The created user.
        """

        if not config.SIGNUPS_ALLOWED:
            raise HTTPException(
                status_code=403,
                detail="Signups are not currently allowed"
            )

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

    async def compile_all_users_for_admin_use(self, caller_user: User) -> Collection[UserRead]:
        """
        Fetches all users in the database. Only includes information relevant to admins.
        """

        if not caller_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="You lack the required permissions to list other users"
            )

        query = await self.db.execute(select(User))
        users = query.scalars().all()

        return Collection(
            items=[
                UserRead(
                    id=user.id,
                    username=user.username,
                    is_admin=user.is_admin,
                ) for user in users
            ]
        )
    
def get_user_service(db: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(db)