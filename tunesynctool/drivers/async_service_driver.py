from abc import ABC, abstractmethod
from typing import List, Optional
import logging
import anyio

from .service_driver import ServiceDriver
from tunesynctool.models import Playlist, Track, Configuration
from .service_mapper import ServiceMapper

"""
Due to the need for async support in the webui's API, this class automatically wraps any ServiceDriver and converts into async.
"""

logger = logging.getLogger(__name__)

class AsyncWrappedServiceDriver:
    """
    Mirrors the ServiceDriver abstract base class's interface with the slight difference that all methods are async.
    
    This does not necessarily mean that the underlying driver is async, but you can now use the wrapped class in an async context without hacks.
    """

    def __init__(
        self,
        sync_driver: ServiceDriver,
    ) -> None:
        self.service_name = sync_driver.service_name
        self.supports_musicbrainz_id_querying = sync_driver.supports_musicbrainz_id_querying
        self.supports_direct_isrc_querying = sync_driver.supports_direct_isrc_querying
        self.sync_driver = sync_driver

        logger.debug(f'Initialized async wrapper for {self.__class__.__name__} driver for {self.service_name} service.')

    async def _wrap_sync(self, fn, *args, **kwargs):
        return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

    async def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        return await self._wrap_sync(
            self.sync_driver.get_user_playlists,
            limit=limit
        )

    async def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        return self._wrap_sync(
            self.sync_driver.get_playlist_tracks,
            playlist_id=playlist_id,
            limit=limit
        )
    
    async def create_playlist(self, name: str) -> Playlist:
        return await self._wrap_sync(
            self.sync_driver.create_playlist,
            name=name
        )
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        return await self._wrap_sync(
            self.sync_driver.add_tracks_to_playlist,
            playlist_id=playlist_id,
            track_ids=track_ids
        )

    async def get_random_track(self) -> Optional[Track]:
        return await self._wrap_sync(
            self.sync_driver.get_random_track
        )
    
    async def get_playlist(self, playlist_id: str) -> Playlist:
        return await self._wrap_sync(
            self.sync_driver.get_playlist,
            playlist_id=playlist_id
        )
    
    async def get_track(self, track_id: str) -> Track:
        return await self._wrap_sync(
            self.sync_driver.get_track,
            track_id=track_id
        )
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        return await self._wrap_sync(
            self.sync_driver.search_tracks,
            query=query,
            limit=limit
        )
    
    async def get_track_by_isrc(self, isrc: str) -> Track:
        return await self._wrap_sync(
            self.sync_driver.get_track_by_isrc,
            isrc=isrc
        )