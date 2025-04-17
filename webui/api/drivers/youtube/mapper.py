from tunesynctool.drivers import ServiceMapper
from tunesynctool.models import Playlist, Track
import isodate

class YouTubeAPIV3Mapper(ServiceMapper):
    """
    Mapper for YouTube API v3.
    """

    def map_playlist(self, data: dict) -> Playlist:
        pass

    def map_track(self, data: dict, additional_data: dict) -> Track:
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

        # These are not returned by the YouTube API
        album_name = None
        additional_artists = []
        track_number = None
        release_year = None
        isrc = None

        return Track(
            title=title,
            album_name=album_name,
            primary_artist=primary_artist,
            additional_artists=additional_artists,
            duration_seconds=duration_seconds,
            track_number=track_number,
            release_year=release_year,
            isrc=isrc,
            service_id=service_id,
            service_name="youtube",
            service_data={
                "track": data,
                "search": data,
            },
        )