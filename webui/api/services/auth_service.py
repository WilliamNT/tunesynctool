from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException

from api.core.security import create_access_token, verify_password, verify_access_token, verify_oauth2_state
from api.models.token import AccessToken
from api.services.user_service import UserService, get_user_service
from api.models.user import User
from api.core.logging import logger
from api.core.security import generate_oauth2_state
from api.models.state import OAuth2StateCreate

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

        logger.debug(f"Handed out JWT for user {user.id}.")
        
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
            logger.warning("JWT signature is valid, however it is missing the subject field. This was likely caused by a bug. Rejecting request.")
            self.raise_unauthorized()

        user = await self.user_service.get_by_id(subject)
        if not user:
            logger.warning("JWT signature is valid, however the user it supposedly belongs to does not exist. Rejecting request.")
            self.raise_unauthorized()

        return user
    
    async def generate_oauth2_state(self, jwt: str, provider_name: str, details: OAuth2StateCreate) -> AccessToken:
        user = await self.resolve_user_from_jwt(jwt)

        logger.info(f"Generating OAuth2 state for user {user.id} and provider \"{provider_name}\".")

        state = generate_oauth2_state(
            user_id=user.id,
            provider_name=provider_name,
            redirect_uri=str(details.redirect_uri),
        )

        return AccessToken(
            access_token=state,
            token_type="state",
            expires_in=timedelta(minutes=10).total_seconds()
        )
    
    async def resolve_user_from_oauth2_state(self, state: str, provider_name: str) -> User:
        """
        Resolves a user from an OAuth2 state.
        
        :param state: The OAuth2 state.
        :return: The user if the state is valid.
        :raises HTTPException: 401 Unauthorized if the state is invalid.
        """

        decoded_state = verify_oauth2_state(
            state=state,
            provider_name=provider_name
        )
        if not decoded_state:
            self.raise_unauthorized()

        user = await self.user_service.get_by_id(decoded_state.user_id)
        if not user:
            self.raise_unauthorized()

        return user
    
def get_auth_service(user_service: Annotated[UserService, Depends(get_user_service)]) -> AuthService:
    return AuthService(user_service)