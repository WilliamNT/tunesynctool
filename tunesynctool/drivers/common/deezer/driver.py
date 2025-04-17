from typing import List, Optional
import asyncio

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import ServiceDriver
from .mapper import DeezerMapper
from .async_driver import AsyncDeezerDriver

from streamrip import Config as StreamRipConfig
from streamrip.client import DeezerClient
from deezer.errors import InvalidQueryException, DataException

class DeezerDriver(ServiceDriver):
    """
    Deezer service driver.

    Synchronous wrapper for AsyncDeezerDriver.
    """
    def __init__(self, config, streamrip_config = None):
        super().__init__(
            service_name='deezer',
            config=config,
            mapper=DeezerMapper(),
            supports_direct_isrc_querying=True
        )

        self._async_driver = AsyncDeezerDriver(config, streamrip_config)

    def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        return asyncio.run(self._async_driver.get_user_playlists(
            limit=limit
        ))

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        return asyncio.run(self._async_driver.get_playlist_tracks(
            playlist_id=playlist_id,
            limit=limit
        ))    
    
    def create_playlist(self, name: str) -> Playlist:
        return asyncio.run(self._async_driver.create_playlist(
            name=name
        ))

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        asyncio.run(self._async_driver.add_tracks_to_playlist(
            playlist_id=playlist_id,
            track_ids=track_ids
        ))

    def get_random_track(self) -> Optional[Track]:
        return asyncio.run(self._async_driver.get_random_track())

    def get_playlist(self, playlist_id: str) -> Playlist:
        return asyncio.run(self._async_driver.get_playlist(
            playlist_id=playlist_id
        ))

    def get_track(self, track_id: str) -> Track:
        return asyncio.run(self._async_driver.get_track(
            track_id=track_id
        ))

    def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        return asyncio.run(self._async_driver.search_tracks(
            query=query,
            limit=limit
        ))
        
    def get_track_by_isrc(self, isrc: str) -> Track:
        return asyncio.run(self._async_driver.get_track_by_isrc(
            isrc=isrc
        ))