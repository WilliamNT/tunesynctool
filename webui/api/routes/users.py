from typing import Annotated
from fastapi import APIRouter, Depends

from api.models.user import UserRead, UserCreate
from api.services.user_service import UserService
from api.core.database import get_session

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate, session: Annotated[UserService, Depends(get_session)]):
    """
    Create a new user.
    """

    service = UserService(session)

    return await service.create_user(user)