from typing import List

from navify.exceptions import PlaylistNotFoundException, ServiceDriverException
from navify.models import Playlist, Configuration, Track
from navify.drivers import ServiceDriver
from .mapper import SubsonicMapper

from libsonic.connection import Connection
from libsonic.errors import DataNotFoundError

class SubsonicDriver(ServiceDriver):
    """Subsonic service driver."""
    
    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='subsonic',
            config=config,
            mapper=SubsonicMapper()
        )

        self.__subsonic = self.__get_connection()

    def __get_connection(self) -> Connection:
        """Configures and returns a Connection object."""

        return Connection(
            baseUrl=self._config.subsonic_base_url,
            port=self._config.subsonic_port,
            username=self._config.subsonic_username,
            password=self._config.subsonic_password,
        )
    
    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        response = self.__subsonic.getPlaylists()
        fetched_playlists = response['playlists'].get('playlist', [])

        if isinstance(fetched_playlists, dict):
            fetched_playlists = [fetched_playlists]

        mapped_playlists = [self._mapper.map_playlist(playlist) for playlist in fetched_playlists[:limit]]

        for playlist in mapped_playlists:
            playlist.service_name = self._service_name

        return mapped_playlists
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        try:
            response = self.__subsonic.getPlaylist(
                pid=playlist_id
            )
            fetched_tracks = response['playlist'].get('entry', [])
            mapped_tracks = [self._mapper.map_track(track) for track in fetched_tracks[:limit]]

            for track in mapped_tracks:
                track.service_name = self._service_name

            return mapped_tracks
        except DataNotFoundError as e:
            raise PlaylistNotFoundException()
        except Exception as e:
            raise ServiceDriverException(f'Subsonic (libsonic) said: {e}')
        
    def create_playlist(self, name: str) -> 'Playlist':
        try:
            response = self.__subsonic.createPlaylist(
                name=name
            )

            return self._mapper.map_playlist(response['playlist'])
        except Exception as e:
            raise ServiceDriverException(f'Subsonic (libsonic) said: {e}')