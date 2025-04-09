from typing import AsyncGenerator
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.core.config import config
from api.models.user import User
from api.core.security import hash_password

engine = create_async_engine(
    url=str(config.SQLALCHEMY_DATABASE_URI)
)

async def initialize_database() -> None:
    """
    Initialize the database by creating all tables.
    """

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        await create_default_user(session)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a new session for the database.
    """

    async with AsyncSession(engine) as session:
        yield session

async def create_default_user(session: AsyncSession) -> None:
    """
    Creates a default admin.
    """

    result = await session.execute(select(User).where(User.username == "admin"))
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        return

    user = User(
        username="admin",
        is_admin=True,
        password_hash=hash_password(config.ADMIN_PASSWORD)
    )

    session.add(user)
    await session.commit()