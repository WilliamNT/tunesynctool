from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from datetime import datetime, timedelta, timezone

from api.core.database import get_session
from api.services.user_service import UserService
from api.models.user import UserLogin

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    path="/login",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Successfully logged in. A cookie has been set.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials.",
        },
    }
)
async def obtain_cookie(user: UserLogin, response: Response, session: Annotated[UserService, Depends(get_session)]):    
    """
    Authenticates via username and password and sets a cookie containing a JWT. The JWT is valid for a limited time.
    """
    
    service = UserService(session)

    token = await service.authenticate(
        username=user.username,
        password=user.password,
    )

    response.set_cookie(
        key="session",
        httponly=True,
        expires=token.expires_at,
        value=token.value,
    )