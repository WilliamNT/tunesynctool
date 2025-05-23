from tunesynctool.drivers import ServiceDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException, PlaylistNotFoundException
from tunesynctool.models import Track, Playlist
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials as GoogleCredentials
from typing import List, Optional
from googleapiclient.errors import HttpError

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
        try:
            results = self.client.playlists().list(
                part="id,snippet,status,contentDetails",
                maxResults=limit,
                mine=True
            ).execute()

            if not results or "items" not in results or len(results["items"]) == 0:
                return []
            
            mapped_playlists = []

            for result in results.get("items", []):
                mapped_playlist = self._mapper.map_playlist(result)
                mapped_playlists.append(mapped_playlist)

            return mapped_playlists
        except Exception as e:
            raise ServiceDriverException(e)

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        try:
            results = self.client.playlistItems().list(
                part="id,snippet,contentDetails",
                maxResults=limit if limit > 0 else None,
                playlistId=playlist_id
            ).execute()

            if not results or "items" not in results or len(results["items"]) == 0:
                return []
            
            result_ids = [result.get("snippet", {}).get("resourceId", {}).get("videoId") for result in results.get("items", [])]

            video_results = self.client.videos().list(
                part="contentDetails",
                id=",".join(result_ids)
            ).execute()

            mapped_videos = []

            for result in results.get("items", []):
                video_id = result.get("snippet", {}).get("resourceId", {}).get("videoId")
                video = filter(lambda x: x.get("id") == video_id, video_results.get("items", []))
                video = list(video)[0]

                mapped_video = self._mapper.map_track_from_playlist_item(result, video)
                mapped_videos.append(mapped_video)

            return mapped_videos
        except HttpError as e:
            if e.status_code == 404:
                raise PlaylistNotFoundException()
            elif e.status_code == 403:
                raise ServiceDriverException("You do not have permission to access this playlist.")
        except Exception as e:
            raise ServiceDriverException(e)

    def create_playlist(self, name: str) -> Playlist:
        try:
            result = self.client.playlists().insert(
                part="snippet",
                body={
                    "snippet": {
                        "title": name
                    }
                }
            ).execute()

            return self._mapper.map_playlist(result)
        except HttpError as e:
            if e.status_code == 403:
                raise ServiceDriverException("Permission error. This is most likely happening because not all required scopes were granted during authorization. Relinking the account should fix this.")
            elif e.status_code == 400:
                raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        try:
            for track_id in track_ids:
                self.client.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": track_id
                            }
                        }
                    }
                ).execute()
        except HttpError as e:
            if e.status_code == 404:
                if isinstance(e.error_details, list) and len(e.error_details) > 0:
                    error = e.error_details[0]
                    if error.get("reason") == "playlistNotFound":
                        raise PlaylistNotFoundException()
                    elif error.get("reason") == "videoNotFound":
                        raise TrackNotFoundException()
            elif e.status_code == 403:
                raise ServiceDriverException("Permission error. This is either happening because the playlist doesn't belong to the linked account or not all required scopes were granted during authorization. Relinking the account should fix this.")
            else:
                raise ServiceDriverException(e) from e
        except Exception as e:
            raise ServiceDriverException(e)

    def get_random_track(self) -> Optional[Track]:
        raise UnsupportedFeatureException("YouTube does not support this feature.")

    def get_playlist(self, playlist_id: str) -> Playlist:
        try:
            result = self.client.playlists().list(
                part="id,snippet,status",
                id=playlist_id
            ).execute()

            if not result or "items" not in result or len(result["items"]) == 0:
                raise PlaylistNotFoundException()
            
            playlist = result["items"][0]

            return self._mapper.map_playlist(playlist)
        except PlaylistNotFoundException:
            raise
        except Exception as e:
            raise ServiceDriverException(e)

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