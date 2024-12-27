from typing import List, Optional

from navify.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException
from navify.models import Playlist, Configuration, Track
from navify.drivers import ServiceDriver
from .mapper import YouTubeMapper

from ytmusicapi import YTMusic
import ytmusicapi

class YouTubeDriver(ServiceDriver):
    """
    Youtube service driver.

    Some functionality may work without providing your credentials, however I don't actively support this use case.
    
    Uses ytmusicapi as its backend:
    https://github.com/sigma67/ytmusicapi
    """

    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='youtube',
            config=config,
            mapper=YouTubeMapper()
        )

        self.__youtube = self.__get_client()

    def __get_client(self) -> YTMusic:
        """Configures and returns a YTMusic object."""

        if not self._config.youtube_request_headers:
            raise ValueError('Youtube request headers are required for this service to work but were not set.')
        
        auth_str = ytmusicapi.setup(
            filepath='ytmusic_navify_browser.json',
            headers_raw=self._config.youtube_request_headers
        )

        return YTMusic(
            auth=auth_str
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        pass

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        pass

    def create_playlist(self, name: str) -> 'Playlist':
        pass

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        pass

    def get_random_track(self) -> Optional['Track']:
        pass

    def get_playlist(self, playlist_id: str) -> 'Playlist':
        pass

    def get_track(self, track_id: str) -> 'Track':
        pass

    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        pass