from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from api.services.auth_service import AuthService, get_auth_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully logged in. ",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials.",
        },
    }
)
async def obtain_token(credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response, auth_service: Annotated[AuthService, Depends(get_auth_service)]):    
    """
    Authenticates via username and password and sets a cookie containing a JWT. The JWT is valid for a limited time.
    """

    jwt = await auth_service.authenticate(
        username=credentials.username,
        password=credentials.password,
    )

    response.set_cookie(
        key="session",
        httponly=True,
        max_age=jwt.expires_in,
        value=jwt.access_token,
    )

    return jwt