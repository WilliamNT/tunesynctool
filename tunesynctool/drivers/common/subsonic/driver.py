from typing import List, Optional

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import ServiceDriver
from .mapper import SubsonicMapper

from libsonic.connection import Connection
from libsonic.errors import DataNotFoundError

class SubsonicDriver(ServiceDriver):
    """
    Subsonic service driver.
    
    Uses libsonic (py-sonic) as its backend:
    https://github.com/crustymonkey/py-sonic
    """
    
    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='subsonic',
            config=config,
            mapper=SubsonicMapper(),
            supports_musicbrainz_id_querying=True
        )

        self.__subsonic = self.__get_connection()

    def __get_connection(self) -> Connection:
        """Configures and returns a Connection object."""

        if not self._config.subsonic_base_url:
            raise ValueError('Subsonic base URL is required for this service to work but was not set.')
        elif not self._config.subsonic_port:
            raise ValueError('Subsonic port is required for this service to work but was not set.')
        elif not self._config.subsonic_username:
            raise ValueError('Subsonic username is required for this service to work but was not set.')
        elif not self._config.subsonic_password:
            raise ValueError('Subsonic password is required for this service to work but was not set.')

        return Connection(
            baseUrl=self._config.subsonic_base_url,
            port=self._config.subsonic_port,
            username=self._config.subsonic_username,
            password=self._config.subsonic_password,
        )
    
    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        try:
            response = self.__subsonic.getPlaylists()
            fetched_playlists = response['playlists'].get('playlist', [])

            if isinstance(fetched_playlists, dict):
                fetched_playlists = [fetched_playlists]

            mapped_playlists = [self._mapper.map_playlist(playlist) for playlist in fetched_playlists[:limit]]

            for playlist in mapped_playlists:
                playlist.service_name = self.service_name

            return mapped_playlists
        except DataNotFoundError as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        try:
            response = self.__subsonic.getPlaylist(
                pid=playlist_id
            )
            fetched_tracks = response['playlist'].get('entry', [])
            mapped_tracks = [self._mapper.map_track(track) for track in fetched_tracks[:limit]]

            for track in mapped_tracks:
                track.service_name = self.service_name

            return mapped_tracks
        except DataNotFoundError as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
        
    def create_playlist(self, name: str) -> 'Playlist':
        try:
            response = self.__subsonic.createPlaylist(
                name=name
            )

            return self._mapper.map_playlist(response['playlist'])
        except Exception as e:
            raise ServiceDriverException(e)
        
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        try:
            self.__subsonic.updatePlaylist(
                lid=playlist_id,
                songIdsToAdd=track_ids
            )
        except Exception as e:
            raise ServiceDriverException(e)
        
    def get_random_track(self) -> Optional['Track']:
        try:
            response = self.__subsonic.getRandomSongs(
                size=1
            )
            fetched_tracks = response['randomSongs'].get('song', [])
            mapped_tracks = [self._mapper.map_track(track) for track in fetched_tracks]

            for track in mapped_tracks:
                track.service_name = self.service_name

            return mapped_tracks[0] if mapped_tracks else None
        except Exception as e:
            raise ServiceDriverException(e)
    
    def get_playlist(self, playlist_id: str) -> 'Playlist':
        try:
            response = self.__subsonic.getPlaylist(
                pid=playlist_id
            )
            return self._mapper.map_playlist(response['playlist'])
        except DataNotFoundError as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
        
    def get_track(self, track_id: str) -> 'Track':
        try:
            response = self.__subsonic.getSong(
                id=track_id
            )
            return self._mapper.map_track(response['song'])
        except DataNotFoundError as e:
            raise TrackNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
        
    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        if not query or len(query) == 0:
            return []

        try:
            response = self.__subsonic.search2(
                query=query,
                artistCount=0,
                albumCount=0,
                songCount=limit,
            )

            fetched_tracks = response['searchResult2'].get('song', [])
            mapped_tracks = [self._mapper.map_track(track) for track in fetched_tracks]

            for track in mapped_tracks:
                track.service_name = self.service_name

            return mapped_tracks
        except Exception as e:
            raise ServiceDriverException(e)