from typing import List, Optional

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import ServiceDriver
from .mapper import SpotifyMapper

from spotipy.oauth2 import SpotifyOAuth
import spotipy
from spotipy.exceptions import SpotifyException

class SpotifyDriver(ServiceDriver):
    """
    Spotify service driver.
    
    Uses spotipy as its backend:
    https://github.com/spotipy-dev/spotipy
    """
    
    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='spotify',
            config=config,
            mapper=SpotifyMapper()
        )

        self.__spotify = spotipy.Spotify(auth_manager=self.__get_auth_manager())
    
    def __get_auth_manager(self) -> SpotifyOAuth:
        """Configures and returns a SpotifyOAuth object."""

        if not self._config.spotify_client_id:
            raise ValueError('Spotify client ID is required for this service to work but was not set.')
        elif not self._config.spotify_client_secret:
            raise ValueError('Spotify client SECRET is required for this service to work but was not set.')
        elif not self._config.spotify_redirect_uri:
            raise ValueError('Spotify redirect URI is required for this service to work but was not set.')
        elif not self._config.spotify_scopes:
            raise ValueError('Spotify SCOPES are required for this service to work but were not set.')

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
            playlist.service_name = self.service_name

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
                track.service_name = self.service_name

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
        
    def get_track(self, track_id: str) -> 'Track':
        try:
            response = self.__spotify.track(track_id)
            return self._mapper.map_track(response)
        except SpotifyException as e:
            raise TrackNotFoundException(f'Spotify (API) said: {e.msg}')
        except Exception as e:
            raise TrackNotFoundException(f'Spotify (spotipy) said: {e}')
        
    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        if not query or len(query) == 0:
            return []
        
        try:
            response = self.__spotify.search(
                q=query,
                limit=limit,
                type='track'
            )

            fetched_tracks = response['tracks']['items']
            mapped_tracks = [self._mapper.map_track(track) for track in fetched_tracks]

            for track in mapped_tracks:
                track.service_name = self.service_name

            return mapped_tracks
        except SpotifyException as e:
            raise PlaylistNotFoundException(f'Spotify (API) said: {e.msg}')
        except Exception as e:
            raise PlaylistNotFoundException(f'Spotify (spotipy) said: {e}')