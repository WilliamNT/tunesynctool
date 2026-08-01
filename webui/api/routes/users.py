from typing import Annotated
from fastapi import APIRouter, Depends, status

from api.models.user import UserRead, UserCreate, UserLookupByIdParams
from api.services.user_service import UserService, get_user_service
from api.core.context import RequestContext, get_request_context
from api.models.collection import Collection

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
        status.HTTP_403_FORBIDDEN: {
            "description": "Registration is not possible at this time."
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

    The instance owner may disable account creation. In that case, an error will be returned.
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

@router.get(
    path="",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "You do not have the required rights to list users."
        },
    },
    summary="List all users on the instance",
    operation_id="getAllUsers",
    name="users:get_all_users",
)
async def get_all_users(
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> Collection[UserRead]:
    """
    Returns information for all user accounts on the current instance.

    Only users with admin rights should call this endpoint, otherwise the request will be rejected.
    """

    return await user_service.compile_all_users_for_admin_use(
        caller_user=request_context.user
    )

@router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "The user has been successfully deleted."
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "The authenticated user is not allowed to delete the specified user."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No user exists with the supplied ID."
        },
        status.HTTP_409_CONFLICT: {
            "description": "The specified user is the last remaining admin and cannot be deleted."
        }
    },
    summary="Delete a user",
    operation_id="deleteUser",
    name="users:delete_user",
)
async def delete_user(
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    filter_query: Annotated[UserLookupByIdParams, Depends()]
) -> None:
    return await user_service.delete_user(
        caller_user=request_context.user,
        user_id=filter_query.id
    )