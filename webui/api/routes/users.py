from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.models.user import UserRead, UserCreate
from api.services.user_service import UserService, get_user_service
from api.core.security import oauth2_scheme
from api.services.auth_service import AuthService, get_auth_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post(
    path="/",
    status_code=201,
    response_model=UserRead,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User created successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "A field is invalid.",
        },
    }
)
async def create_user(user: UserCreate, user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Create a new user.
    """

    return await user_service.create_user(user)

@router.get(
    path="/me",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    responses={
        status.HTTP_200_OK: {
            "description": "User retrieved successfully.",
        }
    }
)
async def get_authenticated_user(auth_service: Annotated[AuthService, Depends(get_auth_service)], jwt: Annotated[str, Depends(oauth2_scheme)]):
    """
    Get the authenticated user.
    """

    return await auth_service.resolve_user_from_jwt(jwt)