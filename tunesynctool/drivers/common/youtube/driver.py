from typing import List, Optional

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import ServiceDriver
from .mapper import YouTubeMapper

from ytmusicapi import YTMusic, OAuthCredentials
from ytmusicapi.exceptions import YTMusicServerError, YTMusicError
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

    def __init__(self, config: Configuration, oauth_credentials: Optional[OAuthCredentials] = None, auth_dict: Optional[dict] = None) -> None:
        """"
        Initializes the YouTube driver with the given configuration and optional OAuth credentials.
        
        Note: if oauth_credentials is provided, you have to also provide the auth_dict parameter but you can safely pass an empty Configuration object.
        :param config: The configuration object containing YouTube credentials. If oauth_credentials is provided, this parameter is ignored.
        :param oauth_credentials: Optional OAuth credentials for authentication. If not provided, the driver will use the request headers from the config.
        :param auth_dict: Optional dictionary containing authentication data. If not provided, the driver will use the request headers from the config.
        :raises ValueError: If any required YouTube credentials are missing in the configuration.
        """

        super().__init__(
            service_name='youtube',
            config=config,
            mapper=YouTubeMapper(),
            supports_direct_isrc_querying=True,
        )

        if oauth_credentials and auth_dict:
            self.__youtube = self.__get_client_from_oauth_credentials(
                oauth_credentials=oauth_credentials,
                auth_dict=auth_dict
            )
        else:
            self.__youtube = self.__get_client_from_browser_headers()

    def __get_client_from_browser_headers(self) -> YTMusic:
        """Configures and returns a YTMusic object."""

        if not self._config.youtube_request_headers:
            raise ValueError('Youtube request headers are required for this service to work but were not set.')
        
        auth_file_path = 'tunesynctool_ytmusic_session.json'

        ytmusicapi.setup(
            filepath=auth_file_path,
            headers_raw=self._config.youtube_request_headers
        )

        return YTMusic(
            auth=auth_file_path
        )
    
    def __get_client_from_oauth_credentials(self, oauth_credentials: OAuthCredentials, auth_dict: dict) -> YTMusic:
        if not oauth_credentials:
            raise ValueError('OAuth credentials are required for this service to work but were not set.')
        if not auth_dict:
            raise ValueError('Auth dict is required for this service to work but was not set.')
        
        return YTMusic(
            auth=auth_dict,
            oauth_credentials=oauth_credentials,
        )

    def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        try:
            response: List[dict] = self.__youtube.get_library_playlists(
                limit=limit
            )
            
            return [self._mapper.map_playlist(playlist) for playlist in response]
        except YTMusicError as e:
            raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        try:
            response: dict = self.__youtube.get_playlist(
                playlistId=playlist_id,
                limit=limit,
            )

            tracks = response.get('tracks', [])
            return [self._mapper.map_track(data=track, additional_data=track) for track in tracks]
        except YTMusicServerError as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def create_playlist(self, name: str) -> Playlist:
        try:
            response = self.__youtube.create_playlist(
                title=name,
                description=''
            )

            return self.get_playlist(
                playlist_id=response
            )
        except YTMusicError as e:
            raise ServiceDriverException(e)

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        try:
            self.__youtube.add_playlist_items(
                playlistId=playlist_id,
                videoIds=track_ids,
                duplicates=True
            )
        except Exception as e:
            raise ServiceDriverException(e)

    def get_random_track(self) -> Optional[Track]:
        raise UnsupportedFeatureException()

    def get_playlist(self, playlist_id: str) -> Playlist:
        try:
            response = self.__youtube.get_playlist(
                playlistId=playlist_id,
                limit=1,
                related=False,
                suggestions_limit=0
            )

            if not response:
                raise PlaylistNotFoundException()
            
            return self._mapper.map_playlist(response)
        except YTMusicServerError as e:
            raise PlaylistNotFoundException(e)
        except Exception as e:
            raise PlaylistNotFoundException(e)

    def get_track(self, track_id: str) -> Track:
        try:
            response: dict = self.__youtube.get_song(
                videoId=track_id,
                signatureTimestamp=None
            )

            if not response or dict(response.get('playabilityStatus', {})).get('status') == 'ERROR':
                raise TrackNotFoundException()

            return self._mapper.map_track(
                data=response,
                additional_data={}
            )
        except YTMusicError as e:
            raise TrackNotFoundException(e)
        except Exception as e:
            raise ServiceDriverException(e)
        
    def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        if not query or len(query) == 0:
            return []
        
        try:
            response: List[dict] = self.__youtube.search(
                query=query,
                limit=limit,
                ignore_spelling=True,
                filter='songs'
            )

            response_tracks: List[dict] = []
            for result in response:
                try:
                    track = self.__youtube.get_song(
                        videoId=result.get('videoId'),
                        signatureTimestamp=None
                    )

                    response_tracks.append(self._mapper.map_track(
                        data=track,
                        additional_data=result
                    ))
                except Exception as e:
                    # If we can't fetch the track, we'll just skip it.
                    continue

            return response_tracks
        except Exception as e:
            raise ServiceDriverException(e)
        
    def get_track_by_isrc(self, isrc: str) -> Track:
        results = self.search_tracks(
            query=isrc.strip().upper(),
            limit=1
        )

        if len(results) == 0:
            raise TrackNotFoundException(f'No track found with ISRC {isrc}')
        
        return results[0]
    
    def get_saved_tracks(self, limit: int = 10) -> List[Track]:
        try:
            response: dict = self.__youtube.get_liked_songs(
                limit=limit
            )

            tracks = response.get('tracks', [])
            return [self._mapper.map_liked_track(data=track) for track in tracks]
        except Exception as e:
            raise ServiceDriverException(e)