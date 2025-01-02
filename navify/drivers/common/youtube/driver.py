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
    Please note that the lack of metadata is not a bug.
    The YouTube API barely returns any metadata beyond the basics like track title, artist and album names.
    
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
        
        auth_file_path = 'navify_ytmusic_session.json'

        ytmusicapi.setup(
            filepath=auth_file_path,
            headers_raw=self._config.youtube_request_headers
        )

        return YTMusic(
            auth=auth_file_path
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        response: List[dict] = self.__youtube.get_library_playlists(
            limit=limit
        )
        
        return [self._mapper.map_playlist(playlist) for playlist in response]

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
        pass

    def create_playlist(self, name: str) -> 'Playlist':
        pass

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        pass

    def get_random_track(self) -> Optional['Track']:
        pass

    def get_playlist(self, playlist_id: str) -> 'Playlist':
        response = self.__youtube.get_playlist(
            playlistId=playlist_id,
            limit=1,
            related=False,
            suggestions_limit=0
        )

        if not response:
            raise PlaylistNotFoundException()
        
        return self._mapper.map_playlist(response)

    def get_track(self, track_id: str) -> 'Track':
        response: dict = self.__youtube.get_song(
            videoId=track_id,
            signatureTimestamp=None
        )

        return self._mapper.map_track(
            data=response,
            additional_data={}
        )
        

    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
        response: List[dict] = self.__youtube.search(
            query=query,
            limit=limit,
            ignore_spelling=True,
            filter='songs'
        )

        response_tracks: List[dict] = []
        for result in response:
            track = self.__youtube.get_song(
                videoId=result.get('videoId'),
                signatureTimestamp=None
            )

            response_tracks.append(self._mapper.map_track(
                data=track,
                additional_data=result
            ))

        return response_tracks