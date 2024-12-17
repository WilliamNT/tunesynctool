from typing import List, Optional

from navify.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException
from navify.models import Playlist, Configuration, Track
from navify.drivers import ServiceDriver
from .mapper import SpotifyMapper

from spotipy.oauth2 import SpotifyOAuth
import spotipy
from spotipy.exceptions import SpotifyException

class SpotifyDriver(ServiceDriver):
    """Spotify service driver."""
    
    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='spotify',
            config=config,
            mapper=SpotifyMapper()
        )

        self.__spotify = spotipy.Spotify(auth_manager=self.__get_auth_manager())
    
    def __get_auth_manager(self) -> SpotifyOAuth:
        """Configures and returns a SpotifyOAuth object."""

        return SpotifyOAuth(
            scope=self._config.spotify_scopes,
            client_id=self._config.spotify_client_id,
            client_secret=self._config.spotify_client_secret,
            redirect_uri=self._config.spotify_redirect_uri
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        response = self.__spotify.current_user_playlists(limit=limit)
        fetched_playlists = response['items']
        mapped_playlists = [self._mapper.map_playlist(playlist) for playlist in fetched_playlists]

        for playlist in mapped_playlists:
            playlist.service_name = self._service_name

        return mapped_playlists

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        try:
            response = self.__spotify.playlist_tracks(
                playlist_id=playlist_id,
                limit=limit
            )
            fetched_tracks = response['items']
            mapped_tracks = [self._mapper.map_track(track['track']) for track in fetched_tracks]

            for track in mapped_tracks:
                track.service_name = self._service_name

            return mapped_tracks
        except SpotifyException as e:
            raise PlaylistNotFoundException(f'Spotify (API) said: {e.msg}')
        except Exception as e:
            raise PlaylistNotFoundException(f'Spotify (spotipy) said: {e}')
        
    def create_playlist(self, name: str) -> 'Playlist':
        try:
            response = self.__spotify.user_playlist_create(
                user=self.__spotify.me()['id'],
                name=name
            )

            return self._mapper.map_playlist(response)
        except Exception as e:
            raise ServiceDriverException(f'Spotify (spotipy) said: {e}')
        
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        try:
            self.__spotify.playlist_add_items(
                playlist_id=playlist_id,
                items=track_ids
            )
        except SpotifyException as e:
            raise PlaylistNotFoundException(f'Spotify (API) said: {e.msg}')
        except Exception as e:
            raise ServiceDriverException(f'Spotify (spotipy) said: {e}')
        
    def get_random_track(self) -> Optional['Track']:
        raise UnsupportedFeatureException('Spotify does not support fetching a random track.')
    
    def get_playlist(self, playlist_id: str) -> 'Playlist':
        try:
            response = self.__spotify.playlist(playlist_id)
            return self._mapper.map_playlist(response)
        except SpotifyException as e:
            raise PlaylistNotFoundException(f'Spotify (API) said: {e.msg}')
        except Exception as e:
            raise PlaylistNotFoundException(f'Spotify (spotipy) said: {e}')