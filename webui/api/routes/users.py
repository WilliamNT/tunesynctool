from fastapi import APIRouter

from api.models.user import UserRead, UserCreate

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate):
    """
    Create a new user.
    """

    # TODO: this is a test endpoint, will replace later

    return UserRead(
        id=1,
        username=user.username,
        is_admin=False,
    )

