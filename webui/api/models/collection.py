from pydantic import BaseModel, Field, computed_field
from typing import Generic, TypeVar, List

T = TypeVar("T")

class Collection(BaseModel, Generic[T]):
    """
    Generic class for a collection of items.
    """

    items: List[T] = Field(
        description="List of items in the collection.",
        default_factory=list
    )

    @computed_field()
    @property
    def item_count(self) -> int:
        """
        The number of items in the collection.
        """

        return len(self.items)

class SearchResultCollection(Collection[T]):
    query: str = Field(description="Search query used to generate the collection.")