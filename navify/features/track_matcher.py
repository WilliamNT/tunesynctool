from typing import List, Optional

from navify.drivers import ServiceDriver
from navify.models import Track
from navify.integrations import Musicbrainz
from navify.utilities import clean_str

class TrackMatcher:
    """
    Attempts to find a matching track between the source and target services.
    """

    def __init__(self, target_driver: ServiceDriver) -> None:
        self._target = target_driver

    def find_match(self, track: Track) -> Optional[Track]:
        """
        Tries to match the track to one available on the target service itself.

        This is a best-effort operation and may not be perfect.
        There is no guarantee that the tracks will be matched correctly or that any will be matched at all.
        """

        if track.service_name == self._target.service_name:
            return self._target.get_track(track.service_id)
        
        # Strategy 1: Using plain old text search
        matched_track = self.__search_with_text(track)
        if track.matches(matched_track):
            return matched_track

        # Stategy 2: Using the ISRC + MusicBrainz ID
        matched_track = self.__search_with_musicbrainz_id(track)
        if track.matches(matched_track):
            return matched_track
        
        # Strategy 3: Using artist discographies
        # matched_track = self.__search_with_discographies(track)
        # if track.matches(matched_track):
        #     return matched_track

        # At this point we haven't found any matches unfortunately
        return None
    
    def __get_musicbrainz_id(self, track: Track) -> Optional[str]:
        """
        Fetches the MusicBrainz ID for a track.
        """

        if track.musicbrainz_id:
            return track.musicbrainz_id

        # musicbrainz_id = Musicbrainz.id_from_isrc(track.isrc)
        # if musicbrainz_id:
        #     return musicbrainz_id
        
        return Musicbrainz.id_from_track(track)
    
    def __search_with_musicbrainz_id(self, track: Track) -> Optional[Track]:
        """
        Searches for tracks using a MusicBrainz ID.
        Requires ISRC or Musicbrainz ID metadata to be available to work.
        """

        if not track.musicbrainz_id:
            track.musicbrainz_id = self.__get_musicbrainz_id(track)
        
        if not track.musicbrainz_id:
            return None
        
        if self._target.supports_musicbrainz_id_querying:
            results = self._target.search_tracks(
                query=track.musicbrainz_id,
                limit=1
            )

            if len(results) > 0:
                return results[0]
        
        return None
    
    def __search_with_text(self, track: Track) -> Optional[Track]:
        """
        Searches for tracks using plain text.
        """

        queries = [
            f'{clean_str(track.primary_artist)} {clean_str(track.title)}',
            f'{clean_str(track.title)}',
            f'{clean_str(track.primary_artist)}'
        ]

        results: List[Track] = []
        for query in queries:
            results.extend(self._target.search_tracks(
                query=query,
                limit=10
            ))

        for result in results:
            if track.matches(result):
                return result
            
        return None
    
    def __search_with_discographies(self, track: Track) -> Optional[Track]:
        """
        Searches for tracks using artist discographies.
        """

        results: List[Track] = []

        for artist in [track.primary_artist] + track.additional_artists:
            results.extend(self._target.search_tracks(
                query=artist,
                limit=10
            ))

        

        return None