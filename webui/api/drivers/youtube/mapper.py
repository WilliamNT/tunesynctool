from tunesynctool.drivers import ServiceMapper
from tunesynctool.models import Playlist, Track
import isodate
from datetime import datetime

class YouTubeAPIV3Mapper(ServiceMapper):
    """
    Mapper for YouTube API v3.
    """

    def map_playlist(self, data: dict) -> Playlist:
        if data.get("kind") != "youtube#playlist":
            raise ValueError(f"Invalid data provided for mapping playlist! Unrecognized resource kind: \"{data.get('kind')}\". Expected \"youtube#playlist\".")
        
        details = data.get("snippet")

        service_id = data.get("id")
        name = details.get("title")
        description = details.get("description")
        author_name = details.get("channelTitle")
        is_public = data.get("status", {}).get("privacyStatus") == "public"
        
        return Playlist(
            name=name,
            author_name=author_name,
            description=description,
            is_public=is_public,
            service_id=service_id,
            service_name="youtube",
            service_data=data
        )

    def map_track(self, data: dict) -> Track:
        if data.get("kind") != "youtube#video":
            raise ValueError(f"Invalid data provided for mapping track! Unrecognized resource kind: \"{data.get('kind')}\". Expected \"youtube#video\".")
        
        details = data.get("snippet")
        if not details:
            raise ValueError("Missing snippet in video response! Either the YouTube API has changed or the \"snippet\" part parameter was not defined correctly in the request.")

        extra_details = data.get("contentDetails")
        if not extra_details:
            raise ValueError("Missing contentDetails in video response! Either the YouTube API has changed or the \"contentDetails\" part parameter was not defined correctly in the request.")

        sevice_id = data.get("id")
        title = details.get("title")
        primary_artist = details.get("channelTitle")
        duration_seconds = isodate.parse_duration(
            extra_details.get("duration", "PT0S")
        ).total_seconds()
        release_year = self._get_year(details.get("publishedAt", "1970-01-01T00:00:00Z"))

        return Track(
            title=title,
            album_name=None,
            primary_artist=primary_artist,
            additional_artists=[],
            duration_seconds=duration_seconds,
            track_number=None,
            release_year=release_year,
            isrc=None,
            service_id=sevice_id,
            service_name="youtube",
            service_data=data
        )

    def map_track_from_search(self, data: dict, additional_data: dict) -> Track:
        if data.get("kind") != "youtube#searchResult" or additional_data.get("kind") != "youtube#video":
            raise ValueError(f"Invalid data provided for mapping track! Unrecognized resource kind: \"{data.get('kind')}\" or \"{additional_data.get('kind')}\". Expected \"youtube#searchResult\" and \"youtube#video\" respectively.")
        
        details = data.get("snippet")
        if not details:
            raise ValueError("Missing snippet in search list response! Either the YouTube API has changed or the \"snippet\" part parameter was not defined correctly in the request.")

        extra_details = additional_data.get("contentDetails")
        if not extra_details:
            raise ValueError("Missing contentDetails in video response! Either the YouTube API has changed or the \"contentDetails\" part parameter was not defined correctly in the request.")

        service_id = data.get("id", {}).get("videoId")
        title = details.get("title")
        primary_artist = details.get("channelTitle")
        duration_seconds = isodate.parse_duration(
            additional_data.get("contentDetails", {}).get("duration", "PT0S")
        ).total_seconds()
        release_year = self._get_year(details.get("publishedAt", "1970-01-01T00:00:00Z"))

        return Track(
            title=title,
            album_name=None,
            primary_artist=primary_artist,
            additional_artists=[],
            duration_seconds=duration_seconds,
            track_number=None,
            release_year=release_year,
            isrc=None,
            service_id=service_id,
            service_name="youtube",
            service_data={
                "track": data,
                "search": data,
            },
        )
    
    def _get_year(self, stamp: str) -> int:
        dt = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        return dt.year
    
    def map_track_from_playlist_item(self, data: dict, additional_data: dict) -> Track:
        if data.get("kind") != "youtube#playlistItem" or additional_data.get("kind") != "youtube#video":
            raise ValueError(f"Invalid data provided for mapping track! Unrecognized resource kind: \"{data.get('kind')}\" or \"{additional_data.get('kind')}\". Expected \"youtube#playlistItem\" and \"youtube#video\" respectively.")
        
        details = data.get("snippet")
        if not details:
            raise ValueError("Missing snippet in search list response! Either the YouTube API has changed or the \"snippet\" part parameter was not defined correctly in the request.")

        extra_details = additional_data.get("contentDetails")
        if not extra_details:
            raise ValueError("Missing contentDetails in video response! Either the YouTube API has changed or the \"contentDetails\" part parameter was not defined correctly in the request.")

        service_id = details.get("resourceId", {}).get("videoId")
        title = details.get("title")
        primary_artist = details.get("videoOwnerChannelTitle")
        duration_seconds = isodate.parse_duration(
            additional_data.get("contentDetails", {}).get("duration", "PT0S")
        ).total_seconds()
        release_year = self._get_year(details.get("publishedAt", "1970-01-01T00:00:00Z"))

        return Track(
            title=title,
            album_name=None,
            primary_artist=primary_artist,
            additional_artists=[],
            duration_seconds=duration_seconds,
            track_number=None,
            release_year=release_year,
            isrc=None,
            service_id=service_id,
            service_name="youtube",
            service_data=data
        )