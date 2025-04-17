from typing import List, Optional

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import AsyncWrappedServiceDriver, ServiceDriver
from .mapper import DeezerMapper

from streamrip import Config as StreamRipConfig
from streamrip.client import DeezerClient
from deezer.errors import InvalidQueryException, DataException

class AsyncDeezerDriver(ServiceDriver, AsyncWrappedServiceDriver):
    """
    Deezer service driver.

    Uses streamrip as its backend:
    https://github.com/nathom/streamrip
    """

    def __init__(self, config: Configuration, streamrip_config: Optional[StreamRipConfig] = None) -> None:
        super().__init__(
            service_name='deezer',
            config=config,
            mapper=DeezerMapper(),
            supports_direct_isrc_querying=True
        )

        self.__deezer = self.__get_client(
            streamrip_config=streamrip_config
        )

    def __get_client(self, streamrip_config: Optional[StreamRipConfig]) -> DeezerClient:
        if not self._config.deezer_arl:
            raise ValueError('Deezer ARL token is required for this service to work but was not set.')
        
        if not streamrip_config:
            streamrip_config = StreamRipConfig.defaults()

        streamrip_config.session.deezer.arl = self._config.deezer_arl

        return DeezerClient(
            config=streamrip_config
        )

    async def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        return UnsupportedFeatureException('Fetching user playlists from Deezer is not supported currently.')

    async def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        try:
            response = await self.__deezer.get_playlist(
                item_id=playlist_id
            )
            
            response_tracks: List[dict] = response.get('tracks', [])
            if limit > 0:
                response_tracks = response_tracks[:min(limit, len(response_tracks))]
            
            return_values = []

            for track in response_tracks:
                return_values.append(self._mapper.map_track(track))

            return return_values
        except InvalidQueryException as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
    
    async def create_playlist(self, name: str) -> Playlist:
        raise UnsupportedFeatureException('Creating playlists on Deezer is not supported currently.')

    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        raise UnsupportedFeatureException('Adding tracks to playlists on Deezer is not supported currently.')

    async def get_random_track(self) -> Optional[Track]:
        raise UnsupportedFeatureException('Fetching random tracks from Deezer is not supported currently.')

    async def get_playlist(self, playlist_id: str) -> Playlist:
        try:
            response = await self.__deezer.get_playlist(
                item_id=playlist_id
            )

            return self._mapper.map_playlist(response)
        except InvalidQueryException as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    async def get_track(self, track_id: str) -> Track:
        try:
            response = await self.__deezer.get_track(
                item_id=track_id
            )

            return self._mapper.map_track(response)
        except InvalidQueryException as e:
            raise TrackNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    async def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        if not query or len(query) == 0:
            return []
        
        try:
            response: List[dict] = await self.__deezer.search(
                media_type='track',
                query=query,
                limit=limit
            )

            if not response or len(response) == 0:
                return []

            response_tracks: List[dict] = response[0].get('data', [])

            # Deezer doesn't return all track information when using their search endpoint
            # so we have to manually query for additional track information.
            # If the limit is set too high, this may lead to unintentional API spamming...
            return_values = []
            for track in response_tracks:
                try:
                    track_id = track.get('id', None)
                    if not track_id:
                        continue

                    result = await self.get_track(
                        track_id=track_id
                    )

                    if result:
                        return_values.append(result)
                except TrackNotFoundException:
                    continue

            return return_values
        except Exception as e:
            raise ServiceDriverException(e)
        
    async def get_track_by_isrc(self, isrc: str) -> Track:
        try:
            response = self.__deezer.client.api.get_track_by_ISRC(
                isrc=isrc.replace('-', '').upper()
            )

            return self._mapper.map_track(response)
        except DataException as e:
            raise TrackNotFoundException(f'No track found with ISRC {isrc}')
        except InvalidQueryException as e:
            raise TrackNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)