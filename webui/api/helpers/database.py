from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


async def create(session: AsyncSession, obj: SQLModel) -> SQLModel:
    """
    Create a new object in the database and return it afterwards.

    :param session: The session to use for the database operation.
    :param obj: The object to create.
    :return: The created object.
    """

    await session.add(obj)
    await session.commit()
    await session.refresh(obj)
    
    return obj