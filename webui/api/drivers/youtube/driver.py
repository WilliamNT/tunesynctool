from tunesynctool.drivers import ServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException
from tunesynctool.models import Track, Playlist
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials as GoogleCredentials
from typing import List, Optional

from .mapper import YouTubeAPIV3Mapper

class YouTubeOAuth2Driver(ServiceDriver):
    """
    YouTube OAuth2 service driver.

    This driver uses official Google SDKs instead of the ytmusicapi package.
    The justification for this is that the ytmusicapi package supports a different kind
    of OAuth2 authentication flow (installed app) and does not support the web application flow.
    """

    def __init__(self, google_credentials: GoogleCredentials) -> None:
        super().__init__(
            service_name="youtube",
            config=None,
            mapper=YouTubeAPIV3Mapper(),
            supports_direct_isrc_querying=False
        )

        self.client = self.__get_client(google_credentials)

    def __get_client(self, google_credentials: GoogleCredentials):
        return build(
            serviceName="youtube",
            version="v3",
            credentials=google_credentials
        )
    
    def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        # playlists = []
        # next_page_token = None

        # while True:
        #     request = self.client.playlists().list(
        #         part="snippet,status",
        #         mine=True,
        #         maxResults=limit,
        #         pageToken=next_page_token
        #     )

        #     response = request.execute()

        #     print(response)
        pass

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        pass

    def create_playlist(self, name: str) -> Playlist:
        pass

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        pass

    def get_random_track(self) -> Optional[Track]:
        pass

    def get_playlist(self, playlist_id: str) -> Playlist:
        pass

    def get_track(self, track_id: str) -> Track:
        try:
            result = self.client.videos().list(
                part="id,snippet,contentDetails",
                id=track_id
            ).execute()

            if not result or "items" not in result or len(result["items"]) == 0:
                raise TrackNotFoundException()
            
            video = result["items"][0]
            
            return self._mapper.map_track(video)
        except TrackNotFoundException:
            raise
        except Exception as e:
            raise ServiceDriverException(e)

    def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        if not query or len(query) == 0:
            return []
        
        try:
            search_results = self.client.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=limit,
                videoCategoryId="10", # Music
                safeSearch="none"
            ).execute()
            
            result_ids = [result.get("id", {}).get("videoId") for result in search_results.get("items", [])]

            video_results = self.client.videos().list(
                part="contentDetails",
                id=",".join(result_ids)
            ).execute()

            mapped_videos = []

            for result in search_results.get("items", []):
                video_id = result.get("id", {}).get("videoId")
                video = filter(lambda x: x.get("id") == video_id, video_results.get("items", []))
                video = list(video)[0]

                mapped_video = self._mapper.map_track_from_search(result, video)
                mapped_videos.append(mapped_video)

            return mapped_videos
        except Exception as e:
            raise ServiceDriverException(e)

    def get_track_by_isrc(self, isrc: str) -> Track:
        raise UnsupportedFeatureException("This feature is not implemented because there is no reliable way to query by ISRC with the YouTube API.")