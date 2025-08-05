from dataclasses import dataclass, field
from typing import Optional, Self
import base64
import json

from tunesynctool.models.track import Track

@dataclass
class Playlist:
    """Represents a playlist."""

    name: str = field(default='Untitled Playlist [@tunesynctool]')
    """Name of the playlist."""

    author_name: Optional[str] = field(default=None)
    """Name of the author of the playlist."""

    description: Optional[str] = field(default=None)
    """Description of the playlist."""

    is_public: bool = field(default=False)
    """Whether the playlist is public or not."""

    service_id: str = field(default=None)
    """Source-service specific ID for the playlist."""

    service_name: str = field(default='unknown')
    """Source service for the track."""

    service_data: Optional[dict] = field(default_factory=dict)
    """Raw JSON response data from the source service."""

    def __str__(self) -> str:
        return f'{self.name} by {self.author_name}'
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: 'Playlist') -> bool:
        return self.service_id == other.service_id and self.service_name == other.service_name
    
    def __hash__(self):
        return hash((self.service_id, self.service_name))
    
    def serialize(self) -> dict:
        """
        Maps the object to a dict.
        """

        service_data = base64.b64encode(json.dumps(self.service_data).encode("utf-8"))

        return {
            "name": self.name,
            "author_name": self.author_name,
            "description": self.description,
            "is_public": self.is_public,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_data": service_data.decode("utf-8")
        }
    
    @staticmethod
    def deserialize(raw_json: dict) -> Self:
        decoded_service_data = None
        if raw_json.get("service_data"):
            decoded_service_data = base64.b64decode(raw_json.get("service_data"))
            decoded_service_data = decoded_service_data.decode("utf-8")
            decoded_service_data = json.loads(decoded_service_data)

        return Playlist(
            name=raw_json.get("name"),
            author_name=raw_json.get("author_name"),
            description=raw_json.get("description"),
            is_public=bool(raw_json.get("is_public", False)),
            service_id=raw_json.get("service_id"),
            service_name=raw_json.get("service_name"),
            service_data=decoded_service_data
        )