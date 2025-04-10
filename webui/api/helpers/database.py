from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


async def create(session: AsyncSession, obj: SQLModel) -> SQLModel:
    """
    Create a new object in the database and return it afterwards.

    :param session: The session to use for the database operation.
    :param obj: The object to create.
    :return: The created object.
    """

    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    
    return obj

async def update(session: AsyncSession, obj: SQLModel) -> SQLModel:
    """
    Update an existing object in the database and return it afterwards.

    :param session: The session to use for the database operation.
    :param obj: The object to update.
    :return: The updated object.
    """

    await session.commit()
    await session.refresh(obj)
    
    return obj

async def delete(session: AsyncSession, obj: SQLModel) -> None:
    """
    Delete an existing object in the database.

    :param session: The session to use for the database operation.
    :param obj: The object to delete.
    :return: None
    """

    await session.delete(obj)
    await session.commit()