from abc import ABC, abstractmethod
from typing import List

from navify.models import Playlist, Track, Configuration

class ServiceDriver(ABC):
    """Defines the interface for a streaming service driver."""

    def __init__(self, service_name: str, config: Configuration) -> None:
        self.service_name = service_name
        self.config = config

    @abstractmethod
    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        """Fetch the authenticated user's playlists from the service."""
        raise NotImplementedError()

    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        """Fetch the tracks in a playlist."""
        raise NotImplementedError()
    
    @abstractmethod
    def create_playlist(self, name: str) -> 'Playlist':
        """Create a new playlist on the service."""
        raise NotImplementedError()