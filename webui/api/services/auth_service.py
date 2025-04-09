from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security import create_access_token, verify_password, verify_access_token
from api.models.token import AccessToken
from api.services.user_service import UserService, get_user_service
from api.models.user import User

class AuthService:
    """
    Service for handling authentication-related operations.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def raise_unauthorized(self):
        """
        Raises an unauthorized exception.
        
        :raises HTTPException: 401 Unauthorized
        """
        
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    
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

    async def authenticate(self, username: str, password: str) -> AccessToken:
        """
        Authenticates a user by username and password.
        
        :param username: The username of the user.
        :param password: The password of the user.
        :param expiration: The expiration time for the JWT token.
        :return: The JWT token if authentication is successful.
        :raises HTTPException: 401 Unauthorized if authentication fails.
        """
        
        user = await self.user_service.get_by_username(username)
        if not user:
            self.raise_unauthorized()

        if not self.verify_password(password, user.password_hash):
            self.raise_unauthorized()

        return create_access_token(
            subject=str(user.id),
            expires_in_days=30,
        )
    
    async def resolve_user_from_jwt(self, jwt: str) -> User:
        """
        Resolves a user from a JWT token.
        
        :param jwt: The JWT token.
        :return: The user if the token is valid.
        :raises HTTPException: 401 Unauthorized if the token is invalid.
        """
        
        subject = verify_access_token(jwt)
        if not subject:
            self.raise_unauthorized()

        user = await self.user_service.get_by_id(subject)
        if not user:
            self.raise_unauthorized()

        return user
    
def get_auth_service(user_service: Annotated[UserService, Depends(get_user_service)]) -> AuthService:
    return AuthService(user_service)