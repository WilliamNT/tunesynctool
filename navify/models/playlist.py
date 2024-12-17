from dataclasses import dataclass, field
from typing import List, Optional

from navify.models.track import Track

@dataclass
class Playlist:
    """Represents a playlist."""

    name: str = field(default='Untitled Playlist [@navify]')
    """Name of the playlist."""

    author_name: Optional[str] = field(default=None)
    """Name of the author of the playlist."""

    description: Optional[str] = field(default=None)
    """Description of the playlist."""

    is_public: bool = field(default=False)
    """Whether the playlist is public or not."""

    tracks: List['Track'] = field(default_factory=list)
    """List of tracks in the playlist."""

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