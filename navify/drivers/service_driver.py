from abc import ABC, abstractmethod
from typing import List, Optional

from navify.models import Playlist, Track, Configuration
from .service_mapper import ServiceMapper

"""
Implementations of this class are responsible for interfacing with various streaming services
and interacting with the authenticated user's data (if applicable).

If a feature is not directly supported by the streaming service, the driver should raise an UnsupportedFeatureException.
Even for features that may not be guaranteed to be supported by all implementations, the default behavior is to raise a NotImplementedError
because it should be up to the individual driver implementations to indicate such limitations by raising an appropriate exception.
"""

class ServiceDriver(ABC):
    """
    Defines the interface for a streaming service driver.
    Do not use directly; subclass this class to implement a custom driver.
    """

    def __init__(self, service_name: str, config: Configuration, mapper: ServiceMapper) -> None:
        self._service_name = service_name
        self._config = config
        self._mapper = mapper

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
    
    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        """Add tracks to a playlist."""
        raise NotImplementedError()
    
    # @abstractmethod
    # def remove_tracks_from_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
    #     """Remove tracks from a playlist."""
    #     raise NotImplementedError()

    @abstractmethod
    def get_random_track(self) -> Optional['Track']:
        """
        Fetch a random track from the service.
        Depending on the streaming service, this may not be supported.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_playlist(self, playlist_id: str) -> 'Playlist':
        """
        Fetch a playlist by its ID.
        """
        raise NotImplementedError()