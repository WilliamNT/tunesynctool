from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from api.models.user import UserCreate, User, UserRead
from api.core.security import hash_password
from api.helpers.database import create
from api.core.database import get_session
from api.core.logging import logger
from api.core.config import config
from api.models.collection import Collection
from api.services.task_service import TaskService, get_task_service
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.models.system import Initiator

class UserService:
    def __init__(self, db: AsyncSession, task_service: TaskService, credentials_service: CredentialsService):
        self.db = db
        self.task_service = task_service
        self.credentials_service = credentials_service

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

    async def _count_admins(self) -> int:
        """
        Returns the number of admin accounts that currently exist.

        :return: The count of users with admin rights.
        """

        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.is_admin == True)  # noqa: E712
        )

        return result.scalar_one()

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

    async def delete_user(self, caller_user: User, user_id: int) -> None:
        """
        Permanently deletes the user account and all belonging data from the system.
        """

        if caller_user.id != user_id and not caller_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to delete this user account"
            )

        query = await self.db.execute(
            select(User).where(User.id == user_id)
        )

        user_to_delete = query.scalar_one_or_none()

        if not user_to_delete:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user_to_delete.is_admin and await self._count_admins() <= 1:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete the last remaining admin account"
            )

        try:
            await self.clean_up_after_user(user_to_delete)
        except Exception as e:
            logger.exception(f"Failed to clean up user with ID {user_to_delete.id}.")

            raise

        await self.db.delete(user_to_delete)
        await self.db.commit()

    async def clean_up_after_user(self, user: User) -> None:
        """
        Removes data owned by the user that lives outside the users table.

        Covers their background tasks (Redis) and their linked accounts and
        other stored service credentials (DB). The user row itself is removed
        by the caller afterwards.

        :param user: The user being removed.
        """

        REASON = "User account is being deleted."

        await self.task_service.delete_tasks_for_user(
            user=user,
            initiator=Initiator.SYSTEM,
            reason=REASON
        )

        await self.credentials_service.delete_all_credentials_for_user(
            user=user,
            log_reason=REASON
        )

def get_user_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)],
) -> UserService:
    return UserService(
        db=db,
        task_service=task_service,
        credentials_service=credentials_service,
    )