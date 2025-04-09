from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import UserCreate, User
from api.core.security import hash_password
from api.helpers.database import create

class UserService:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create(self, user: UserCreate) -> User:
        """
        Creates a new user in the database and returns it afterwards.
        
        :param user: The user to create.
        :return: The created user.
        """

        new_user = User(
            username=user.username,
            password_hash=hash_password(user.password),
            is_admin=False,
        )

        return await create(
            session=self.db,
            obj=new_user,
        )