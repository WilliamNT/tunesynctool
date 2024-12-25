from typing import List, Optional
import asyncio

from navify.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException
from navify.models import Playlist, Configuration, Track
from navify.drivers import ServiceDriver
from .mapper import DeezerMapper

from streamrip import Config as StreamRipConfig
from streamrip.client import DeezerClient

class DeezerDriver(ServiceDriver):
    """
    WARNING: CONSIDER THIS DRIVER EXPERIMENTAL. ONLY READ OPERATIONS ARE SUPPORTED.
    Deezer service driver.

    Uses streamrip as its backend:
    https://github.com/nathom/streamrip
    """

    def __init__(self, config: Configuration, streamrip_config: StreamRipConfig) -> None:
        super().__init__(
            service_name='deezer',
            config=config,
            mapper=DeezerMapper()
        )

        self.__deezer = self.__get_client(
            streamrip_config=streamrip_config
        )

    def __get_client(self, streamrip_config: StreamRipConfig) -> DeezerClient:
        return DeezerClient(
            config=streamrip_config
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        return UnsupportedFeatureException('Fetching user playlists from Deezer is not supported currently.')

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        response = asyncio.run(self.__deezer.get_playlist(
            item_id=playlist_id
        ))
        
        response_tracks: List[dict] = response.get('tracks', [])[:limit]
        
        return_values = []

        for track in response_tracks:
            return_values.append(self._mapper.map_track(track))

        return return_values
    
    def create_playlist(self, name: str) -> 'Playlist':
        raise UnsupportedFeatureException('Creating playlists on Deezer is not supported currently.')

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        raise UnsupportedFeatureException('Adding tracks to playlists on Deezer is not supported currently.')

    def get_random_track(self) -> Optional['Track']:
        raise UnsupportedFeatureException('Fetching random tracks from Deezer is not supported currently.')

    def get_playlist(self, playlist_id: str) -> 'Playlist':
        response = asyncio.run(self.__deezer.get_playlist(
            item_id=playlist_id
        ))

        return self._mapper.map_playlist(response)

    def get_track(self, track_id: str) -> 'Track':
        response = asyncio.run(self.__deezer.get_track(
            item_id=track_id
        ))

        return self._mapper.map_track(response)

    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        response: List[dict] = asyncio.run(self.__deezer.search(
            media_type='track',
            query=query,
            limit=limit
        ))

        response_tracks: List[dict] = response[0].get('data', [])

        # Deezer doesn't return all track information when using their search endpoint
        # so we have to manually query for additional track information.
        # If the limit is set too high, this may lead to unintentional API spamming...
        return_values = []
        for track in response_tracks:
            track_id = track.get('id', None)
            if not track_id:
                continue

            result = self.get_track(
                track_id=track_id
            )

            if result:
                return_values.append(result)

        return return_values