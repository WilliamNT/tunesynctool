from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.models.user import UserRead, UserCreate
from api.services.user_service import UserService, get_user_service
from api.core.context import RequestContext, get_request_context

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    path="",
    status_code=201,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User created successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "A field is invalid.",
        },
    },
    summary="Create a new user",
    operation_id="createUser",
    name="users:create_user",
)
async def create_user(
    user: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserRead:
    """
    Create a new user.

    Anyone may create a new account for themselves, assuming their chosen username is not already taken.
    """

    return await user_service.create_user(user)

@router.get(
    path="/me",
    summary="Get information about the authenticated user",
    operation_id="getAuthenticatedUser",
    name="users:get_authenticated_user",
)
async def get_authenticated_user(
    request_context: Annotated[RequestContext, Depends(get_request_context)]
) -> UserRead:
    """
    Get the authenticated user.
    """

    return request_context.user