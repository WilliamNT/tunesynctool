from typing import List, Optional

from tunesynctool.exceptions import PlaylistNotFoundException, ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Playlist, Configuration, Track
from tunesynctool.drivers import ServiceDriver
from .mapper import YouTubeMapper

from ytmusicapi import YTMusic
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
        
        auth_file_path = 'tunesynctool_ytmusic_session.json'

        ytmusicapi.setup(
            filepath=auth_file_path,
            headers_raw=self._config.youtube_request_headers
        )

        return YTMusic(
            auth=auth_file_path
        )

    def get_user_playlists(self, limit: int = 25) -> List['Playlist']:
        try:
            response: List[dict] = self.__youtube.get_library_playlists(
                limit=limit
            )
            
            return [self._mapper.map_playlist(playlist) for playlist in response]
        except YTMusicError as e:
            raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List['Track']:
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

    def create_playlist(self, name: str) -> 'Playlist':
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
        self.__youtube.add_playlist_items(
            playlistId=playlist_id,
            videoIds=track_ids,
            duplicates=True
        )

    def get_random_track(self) -> Optional['Track']:
        raise UnsupportedFeatureException()

    def get_playlist(self, playlist_id: str) -> 'Playlist':
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

    def get_track(self, track_id: str) -> 'Track':
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
        
    def search_tracks(self, query: str, limit: int = 10) -> List['Track']:
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
                pass

        return response_tracks