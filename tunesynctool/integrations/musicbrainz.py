from typing import Optional
import logging

from tunesynctool.models import Track
from tunesynctool.utilities import clean_str

import musicbrainzngs

musicbrainzngs.set_useragent("tunesynctool", "1.0", "https://github.com/WilliamNT/tunesynctool")
logger = logging.getLogger(__name__)

class Musicbrainz:
    """Responsible for interacting with the Musicbrainz API."""

    @staticmethod
    def id_from_isrc(isrc: str) -> Optional[str]:
        """Fetches the Musicbrainz ID for a track given its ISRC."""
        
        try:
            response = musicbrainzngs.search_recordings(isrc=isrc)
            return Musicbrainz.__get_id(response)
        except musicbrainzngs.MusicBrainzError as e:
            logger.warning(f"Musicbrainz lookup failed for track (ISRC: {isrc}). Reason: {e}")
            return None
    
    @staticmethod
    def id_from_track(track: Track) -> Optional[str]:
        """
        Fetches the Musicbrainz ID for a track using its metadata.
        The less metadata, the less accurate the result.
        """
        
        if track.musicbrainz_id:
            return track.musicbrainz_id
        
        try:
            response: dict = musicbrainzngs.search_recordings(
                query=clean_str(track.title),
                artist=track.primary_artist,
                date=track.release_year,
                alias=track.title,
                isrc=track.isrc
            )

            return Musicbrainz.__get_id(response)
        except musicbrainzngs.MusicBrainzError as e:
            logger.warning(f"Musicbrainz lookup failed for track {track}. Reason: {e}")
            return None
    
    @staticmethod
    def __get_id(data: dict) -> Optional[str]:
        items = data.get('recording-list', [])

        if len(items) == 0:
            return None
        
        return items[0].get('id', None)