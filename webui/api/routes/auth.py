from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from api.services.auth_service import AuthService, get_auth_service
from api.models.token import AccessToken

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=AccessToken,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully logged in. ",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials.",
        },
    },
    summary="Obtain a JWT token (and cookie)",
    operation_id="getToken",
)
async def obtain_token(credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response, auth_service: Annotated[AuthService, Depends(get_auth_service)]):    
    """
    Generates a bearer JWT for the user.

    Requires the user to provide their username and password.
    The JWT is returned in the response body **and** as a cookie.
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