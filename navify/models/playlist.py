from dataclasses import dataclass, field
from typing import List, Optional

from navify.models.track import Track

@dataclass
class Playlist:
    """Represents a playlist."""

    name: str = field(default=None)
    """Name of the playlist."""

    author_name: str = field(default=None)
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

    service_data: Optional[dict] = field(default=None)
    """Raw JSON response data from the source service."""

    def __str__(self) -> str:
        return f'{self.name} by {self.author_name}'
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: 'Playlist') -> bool:
        return self.service_id == other.service_id and self.service_name == other.service_name
    
    @classmethod
    def from_subsonic_json(cls, data: dict) -> 'Playlist':
        """Create a Playlist instance from a Subsonic API response."""
        
        service_id = data.get('id')
        name = data.get('name')
        description = data.get('comment')
        is_public = data.get('public', False)
        author_name = data.get('owner')
        
        return cls(
            service_id=service_id,
            service_name='subsonic',
            name=name,
            description=description,
            is_public=is_public,
            author_name=author_name,
            service_data=data
        )

    @classmethod
    def from_spotify_json(cls, data: dict) -> 'Playlist':
        """Create a Playlist instance from a Spotify API response."""
        
        service_id = data.get('id')
        name = data.get('name')
        description = data.get('description')
        is_public = data.get('public', False)
        author_name = data.get('owner').get('display_name')
        
        return cls(
            service_id=service_id,
            service_name='spotify',
            name=name,
            description=description,
            is_public=is_public,
            author_name=author_name,
            service_data=data
        )