from typing import Annotated
from fastapi import Depends
from api.models.user import User
from api.services.auth_service import AuthService, get_auth_service
from api.core.security import oauth2_scheme

class RequestContext:
    def __init__(self, user: User, jwt: str):
        self.user = user
        self.jwt = jwt

async def get_request_context(
        jwt: Annotated[str, Depends(oauth2_scheme)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> RequestContext:
    user = await auth_service.resolve_user_from_jwt(jwt)

    return RequestContext(
        user=user,
        jwt=jwt
    )