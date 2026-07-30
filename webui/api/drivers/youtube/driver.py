from tunesynctool.drivers import ServiceDriver, YouTubeDriver as LegacyYouTubeDriver
from tunesynctool.exceptions import ServiceDriverException, UnsupportedFeatureException, TrackNotFoundException, PlaylistNotFoundException
from tunesynctool.models import Track, Playlist
from tunesynctool.models import Configuration as LegacyConfiguration
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials as GoogleCredentials
from typing import List, Optional
from googleapiclient.errors import HttpError

from .mapper import YouTubeAPIV3Mapper
from .exception import PrivateResourceException
from api.helpers.ytmusicapi import CustomYTMusicAPIOAuthCredentials
from api.core.config import config

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
        self.__legacy_driver = self.__get_legacy_driver(google_credentials)

    def __get_client(self, google_credentials: GoogleCredentials):
        return build(
            serviceName="youtube",
            version="v3",
            credentials=google_credentials
        )

    def __get_legacy_driver(self, google_credentials: GoogleCredentials) -> ServiceDriver:
        oauth_credentials = CustomYTMusicAPIOAuthCredentials(
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            google_credentials=google_credentials,
        )

        return LegacyYouTubeDriver(
            config=LegacyConfiguration(),
            oauth_credentials=oauth_credentials,
            auth_dict=oauth_credentials.custom_get_auth_dict(),
        )

    def get_user_playlists(self, limit: int = 25) -> List[Playlist]:
        try:
            mapped_playlists = []
            next_page_token = None

            while True:
                results = self.client.playlists().list(
                    part="id,snippet,status,contentDetails",
                    maxResults=50,
                    mine=True,
                    pageToken=next_page_token
                ).execute()

                if not results or "items" not in results or len(results["items"]) == 0:
                    break

                for result in results.get("items", []):
                    mapped_playlists.append(self._mapper.map_playlist(result))

                if limit > 0 and len(mapped_playlists) >= limit:
                    break

                next_page_token = results.get("nextPageToken")
                if not next_page_token:
                    break

            if limit > 0:
                return mapped_playlists[:limit]

            return mapped_playlists
        except HttpError as e:
            if e.status_code == 403:
                raise PrivateResourceException("Permission error. This is most likely happening because not all required scopes were granted during authorization. Relinking the account should fix this.")
            raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        try:
            mapped_videos = []
            next_page_token = None

            while True:
                results = self.client.playlistItems().list(
                    part="id,snippet,contentDetails",
                    maxResults=50,
                    playlistId=playlist_id,
                    pageToken=next_page_token
                ).execute()

                if not results or "items" not in results or len(results["items"]) == 0:
                    break

                result_ids = [
                    result.get("snippet", {}).get("resourceId", {}).get("videoId")
                    for result in results.get("items", [])
                    if result.get("snippet", {}).get("resourceId", {}).get("videoId")
                ]

                if result_ids:
                    video_results = self.client.videos().list(
                        part="contentDetails",
                        id=",".join(result_ids)
                    ).execute()
                else:
                    video_results = {"items": []}

                videos_by_id = {
                    video.get("id"): video
                    for video in video_results.get("items", [])
                    if video.get("id")
                }

                for result in results.get("items", []):
                    video_id = result.get("snippet", {}).get("resourceId", {}).get("videoId")
                    video = videos_by_id.get(video_id)

                    if not video:
                        continue

                    mapped_videos.append(self._mapper.map_track_from_playlist_item(result, video))

                if limit > 0 and len(mapped_videos) >= limit:
                    break

                next_page_token = results.get("nextPageToken")
                if not next_page_token:
                    break

            if limit > 0:
                return mapped_videos[:limit]

            return mapped_videos
        except HttpError as e:
            if e.status_code == 404:
                raise PlaylistNotFoundException()
            elif e.status_code == 403:
                raise PrivateResourceException("You do not have permission to access this playlist.")
            raise ServiceDriverException(e)
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
                raise PrivateResourceException("Permission error. This is most likely happening because not all required scopes were granted during authorization. Relinking the account should fix this.")
            raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        try:
            for track_id in track_ids:
                try:
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
                            if e.error_details[0].get("reason") == "videoNotFound":
                                continue
                    raise
        except HttpError as e:
            if e.status_code == 404:
                if isinstance(e.error_details, list) and len(e.error_details) > 0:
                    error = e.error_details[0]
                    if error.get("reason") == "playlistNotFound":
                        raise PlaylistNotFoundException()
            elif e.status_code == 403:
                raise PrivateResourceException("Permission error. This is either happening because the playlist doesn't belong to the linked account or not all required scopes were granted during authorization. Relinking the account should fix this.")
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
        except HttpError as e:
            if e.status_code == 403:
                raise PrivateResourceException("Permission error. This is either happening because the playlist doesn't belong to the linked account or not all required scopes were granted during authorization. Relinking the account should fix this.")
            raise ServiceDriverException(e)
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
        except HttpError as e:
            if self._is_rate_limit_exception(e):
                return self.__legacy_driver.get_track(
                    track_id=track_id,
                )
            elif e.status_code == 403:
                raise PrivateResourceException("Permission error. This is either happening because the track doesn't belong to the linked account, the user does not have permission to access it, or not all required scopes were granted during authorization. Relinking the account may fix this.")
            raise ServiceDriverException(e)
        except ServiceDriverException:
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

            result_ids = [
                result.get("id", {}).get("videoId")
                for result in search_results.get("items", [])
                if result.get("id", {}).get("videoId")
            ]

            if len(result_ids) == 0:
                return []

            video_results = self.client.videos().list(
                part="id,snippet,contentDetails",
                id=",".join(result_ids)
            ).execute()
            videos_by_id = {
                video.get("id"): video
                for video in video_results.get("items", [])
                if video.get("id")
            }

            mapped_videos = []

            for result in search_results.get("items", []):
                video_id = result.get("id", {}).get("videoId")
                video = videos_by_id.get(video_id)

                if not video:
                    continue

                mapped_video = self._mapper.map_track_from_search(result, video)
                mapped_videos.append(mapped_video)

            return mapped_videos
        except HttpError as e:
            if self._is_rate_limit_exception(e):
                return self.__legacy_driver.search_tracks(
                    query=query,
                    limit=limit,
                )
            raise ServiceDriverException(e)
        except Exception as e:
            raise ServiceDriverException(e)

    def get_track_by_isrc(self, isrc: str) -> Track:
        raise UnsupportedFeatureException("This feature is not implemented because there is no reliable way to query by ISRC with the YouTube API.")

    def get_saved_tracks(self, limit: int = 10) -> List[Track]:
        return self.get_playlist_tracks(
            playlist_id="LM",
            limit=limit,
        )

    def _is_rate_limit_exception(self, e: HttpError) -> bool:
        error_codes = [
            "quotaExceeded",
            "rateLimitExceeded",
            "userRateLimitExceeded",
        ]

        details = e.error_details
        if isinstance(details, dict):
            details = [details]

        if not isinstance(details, list):
            return False

        return any(
            isinstance(error, dict) and error.get("reason") in error_codes
            for error in details
        )
