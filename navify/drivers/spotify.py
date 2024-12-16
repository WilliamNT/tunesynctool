from typing import List

from navify.exceptions import PlaylistNotFoundException, ServiceDriverException
from navify.models import Playlist, Configuration, Track
from . import ServiceDriver

from spotipy.oauth2 import SpotifyOAuth
import spotipy
from spotipy.exceptions import SpotifyException

class SpotifyDriver(ServiceDriver):
    """Spotify service driver."""
    
    def __init__(self, config: Configuration) -> None:
        super().__init__(
            service_name='spotify',
            config=config
        )

        self.__spotify = spotipy.Spotify(auth_manager=self.__get_auth_manager())
    
    def __get_auth_manager(self) -> SpotifyOAuth:
        """Configures and returns a SpotifyOAuth object."""

        return SpotifyOAuth(
            scope=self.config.spotify_scopes,
            client_id=self.config.spotify_client_id,
            client_secret=self.config.spotify_client_secret,
            redirect_uri=self.config.spotify_redirect_uri
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        response = self.__spotify.current_user_playlists(limit=limit)
        fetched_playlists = response['items']
        mapped_playlists = [Playlist.from_spotify_json(playlist) for playlist in fetched_playlists]

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
            mapped_tracks = [Track.from_spotify_json(track['track']) for track in fetched_tracks]

            for track in mapped_tracks:
                track.service_name = self.service_name

            return mapped_tracks
        except SpotifyException as e:
            raise PlaylistNotFoundException(f'Spotify said: {e.msg}')
        except Exception as e:
            raise PlaylistNotFoundException(f'Spotify (spotipy) said: {e}')
        
    def create_playlist(self, name: str) -> 'Playlist':
        try:
            response = self.__spotify.user_playlist_create(
                user=self.__spotify.me()['id'],
                name=name
            )

            return Playlist.from_spotify_json(response)
        except Exception as e:
            raise ServiceDriverException(f'Subsonic (libsonic) said: {e}')