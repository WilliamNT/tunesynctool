from typing import Optional

from navify.models import Track
from navify.utilities import clean_str

import musicbrainzngs

musicbrainzngs.set_useragent("Navify", "0.1", "https://github.com/WilliamNT/navify")

class Musicbrainz:
    """Responsible for interacting with the Musicbrainz API."""

    @staticmethod
    def id_from_isrc(isrc: str) -> Optional[str]:
        """Fetches the Musicbrainz ID for a track given its ISRC."""
            
        response = musicbrainzngs.search_recordings(isrc=isrc)
        return Musicbrainz.__get_id(response)
    
    @staticmethod
    def id_from_track(track: Track) -> Optional[str]:
        """
        Fetches the Musicbrainz ID for a track using its metadata.
        The less metadata, the less accurate the result.
        """
        
        if track.musicbrainz_id:
            return track.musicbrainz_id
        
        response: dict = musicbrainzngs.search_recordings(
            query=clean_str(track.title),
            artist=track.primary_artist,
            date=track.release_year,
            alias=track.title,
            isrc=track.isrc
        )

        return Musicbrainz.__get_id(response)
    
    @staticmethod
    def __get_id(data: dict) -> Optional[str]:
        items = data.get('recording-list', [])

        if len(items) == 0:
            return None
        
        return items[0].get('id', None)