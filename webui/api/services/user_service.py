from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException

from api.models.user import UserCreate, User
from api.core.security import create_access_token, hash_password, verify_password
from api.helpers.database import create
from api.models.token import Token

class UserService:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_user(self, user: UserCreate) -> User:
        """
        Creates a new user in the database and returns it afterwards.
        
        :param user: The user to create.
        :return: The created user.
        """

        new_user = User(
            username=user.username,
            password_hash=hash_password(user.password),
            is_admin=False,
        )

        return await create(
            session=self.db,
            obj=new_user,
        )
    
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
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a password against a hashed password.
        
        :param plain_password: The plain password to verify.
        :param hashed_password: The hashed password to verify against.
        :return: True if the password matches, otherwise False.
        """
        
        return verify_password(
            plain_password=plain_password,
            hashed_password=hashed_password,
        )

    async def authenticate(self, username: str, password: str) -> Token:
        """
        Authenticates a user by username and password.
        
        :param username: The username of the user.
        :param password: The password of the user.
        :param expiration: The expiration time for the JWT token.
        :return: The JWT token if authentication is successful.
        :raises HTTPException: 401 Unauthorized if authentication fails.
        """
        
        user = await self.get_by_username(username)
        if not user:
            self.raise_unauthorized()

        if not self.verify_password(password, user.password_hash):
            self.raise_unauthorized()

        expiration = datetime.now(timezone.utc) + timedelta(days=30)

        return create_access_token(
            subject=str(user.id),
            expiration=expiration,
        )
        
    def raise_unauthorized(self):
        """
        Raises an unauthorized exception.
        
        :raises HTTPException: 401 Unauthorized
        """
        
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )