from sqlmodel import SQLModel, create_engine

from api.core.config import config
from api.models.user import User

engine = create_engine(
    url=str(config.SQLALCHEMY_DATABASE_URI)
)

def initialize_database() -> None:
    """
    Initialize the database by creating all tables.
    """

    SQLModel.metadata.create_all(engine)