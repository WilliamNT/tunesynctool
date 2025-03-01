from abc import ABC, abstractmethod
from typing import List, Optional

from tunesynctool.models import Playlist, Track, Configuration
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

    def __init__(
        self,
        service_name: str,
        config: Configuration,
        mapper: ServiceMapper,
        supports_musicbrainz_id_querying: bool = False,
        supports_direct_isrc_querying: bool = False,
    ) -> None:
        self.service_name = service_name
        self._config = config
        self._mapper = mapper
        self.supports_musicbrainz_id_querying = supports_musicbrainz_id_querying
        self.supports_direct_isrc_querying = supports_direct_isrc_querying

    @abstractmethod
    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        """
        Fetch the authenticated user's playlists from the service.

        :param limit: The maximum number of playlists to fetch.
        :return: A list of Playlist objects.
        :raises: ServiceDriverException if an unknown error occurs while fetching the playlists.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        """
        Fetch the tracks in a playlist.
        
        :param playlist_id: The ID of the playlist to fetch.
        :param limit: The maximum number of tracks to fetch.
        :return: A list of Track objects.
        :raises: PlaylistNotFoundException if the playlist does not exist.
        :raises: ServiceDriverException if an unknown error occurs while fetching the tracks.
        """

        raise NotImplementedError()
    
    @abstractmethod
    def create_playlist(self, name: str) -> 'Playlist':
        """
        Create a new playlist on the service.
        
        :param name: The name of the playlist to create.
        :return: The created Playlist object.
        :raises: ServiceDriverException if an unknown error occurs while creating the playlist.
        """

        raise NotImplementedError()
    
    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        """
        Add tracks to a playlist. Does not validate if the tracks are already in the playlist or if they exist.
        
        :param playlist_id: The ID of the playlist to add tracks to.
        :param track_ids: The IDs of the tracks to add.
        :raises: ServiceDriverException if an unknown error occurs while adding the tracks.
        """

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

        :return: A Track object.
        :raises: UnsupportedFeatureException if the service does not support fetching a random track.
        :raises: ServiceDriverException if an unknown error occurs while fetching the track.
        """

        raise NotImplementedError()
    
    @abstractmethod
    def get_playlist(self, playlist_id: str) -> 'Playlist':
        """
        Fetch a playlist by its ID.

        :param playlist_id: The ID of the playlist to fetch.
        :return: The Playlist object.
        :raises: PlaylistNotFoundException if the playlist does not exist.
        :raises: ServiceDriverException if an unknown error occurs while fetching the playlist.
        """

        raise NotImplementedError()
    
    @abstractmethod
    def get_track(self, track_id: str) -> 'Track':
        """
        Fetch a track by its ID.

        :param track_id: The ID of the track to fetch.
        :return: The Track object.
        :raises: TrackNotFoundException if the track does not exist.
        :raises: ServiceDriverException if an unknown error occurs while fetching the track.
        """

        raise NotImplementedError()
    
    @abstractmethod
    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        """
        Search for tracks by a query.

        :param query: The search query.
        :param limit: The maximum number of tracks to fetch.
        :return: A list of Track objects.
        :raises: ServiceDriverException if an unknown error occurs while searching for tracks.
        """
        
        raise NotImplementedError()
    
    @abstractmethod
    def get_track_by_isrc(self, isrc: str) -> 'Track':
        """
        Fetch a track by its ISRC.

        :param isrc: The ISRC of the track to fetch.
        :return: The Track object.
        :raises: TrackNotFoundException if the track does not exist.
        :raises: ServiceDriverException if an unknown error occurs while fetching the track.
        """

        raise NotImplementedError()