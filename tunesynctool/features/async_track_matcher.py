from typing import List, Optional
import logging

from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import TrackNotFoundException
from tunesynctool.models import Track
from tunesynctool.integrations import Musicbrainz
from tunesynctool.utilities import clean_str, batch

logger = logging.getLogger(__name__)

class AsyncTrackMatcher:
    """
    Async version of the TrackMatcher class.
    """

    def __init__(self, target_driver: AsyncWrappedServiceDriver) -> None:
        self._target = target_driver

    async def find_match(self, track: Track) -> Optional[Track]:
        """
        Tries to match the track to one available on the target service itself.

        This is a best-effort operation and may not be perfect.
        There is no guarantee that the tracks will be matched correctly or that any will be matched at all.

        :param track: The track to match.
        :return: The matched track, if any.
        """

        # Strategy 0: If the track is suspected to originate from the same service, try to fetch it directly
        matched_track = await self.__search_on_origin_service(track)
        if track.matches(matched_track):
            logger.debug(f'Success: matched track {track} to {matched_track} using origin service.')
            return matched_track
        
        # Strategy 1: If the track has an ISRC, try to search for it directly
        matched_track = await self.__search_by_isrc_only(track)
        if track.matches(matched_track):
            logger.debug(f'Success: matched track {track} to {matched_track} using direct ISRC. querying.')
            return matched_track
        
        # Strategy 2: Using plain old text search
        matched_track = await self.__search_with_text(track)
        if track.matches(matched_track):
            logger.debug(f'Success: matched track {track} to {matched_track} using text search.')
            return matched_track

        # Stategy 3: Using the ISRC + MusicBrainz ID
        matched_track = await self.__search_with_musicbrainz_id(track)
        if track.matches(matched_track):
            logger.debug(f'Success: matched track {track} to {matched_track} using its MusicBrainz ID.')
            return matched_track

        # At this point we haven't found any matches unfortunately
        logger.debug(f'Failure: could not find a match for track {track}.')
        return None
    
    def __get_musicbrainz_id(self, track: Track) -> Optional[str]:
        """
        Fetches the MusicBrainz ID for a track.

        :param track: The track to fetch the ID for.
        :return: The MusicBrainz ID, if available.
        """

        if track.musicbrainz_id:
            return track.musicbrainz_id
        
        return Musicbrainz.id_from_track(track)
    
    async def __search_with_musicbrainz_id(self, track: Track) -> Optional[Track]:
        """
        Searches for tracks using a MusicBrainz ID.
        Requires ISRC or Musicbrainz ID metadata to be available to work.

        :param track: The track to search for.
        :return: The matched track, if any.
        """

        if not track.musicbrainz_id:
            track.musicbrainz_id = self.__get_musicbrainz_id(track)
        
        if not track.musicbrainz_id:
            return None
        
        if self._target.supports_musicbrainz_id_querying:
            results = await self._target.search_tracks(
                query=track.musicbrainz_id,
                limit=1
            )

            if len(results) > 0:
                return results[0]
        
        return None
    
    async def __search_with_queries(self, query_attempts: List[str], reference_track: Track) -> Optional[Track]:
        """
        Searches for tracks using a list of queries and returns the most likely match.

        Does multiple rounds with filtering.

        :param query_attempts: A list of queries to attempt.
        :param reference_track: The track to search for.
        :return: The matched track, if any.
        """

        results: List[Track] = []

        for queries in batch(query_attempts, 5):
            subresults: List[Track] = []
            
            for query in queries:
                search_results = await self._target.search_tracks(
                    query=query,
                    limit=5
                )

                if len(search_results) == 0:
                    continue

                subresults.append(max(search_results, key=lambda x: x.similarity(reference_track)))

            if len(subresults) == 0:
                continue

            best_match = max(subresults, key=lambda x: x.similarity(reference_track))
            logger.debug(f'Found match {best_match} for query {query} with similarity {best_match.similarity(reference_track)}')
            results.append(best_match)

        maybe_match = None
        if len(results) > 0 :
            maybe_match = max(results, key=lambda x: x.similarity(reference_track))
            
        return maybe_match
        
    async def __search_with_text(self, track: Track) -> Optional[Track]:
        """
        Searches for tracks using plain text.

        :param track: The track to search for.
        :return: The matched track, if any.
        """

        queries = []

        if track.title:
            queries.append(clean_str(track.title))
            queries.append(track.title)

        if track.primary_artist:
            queries.append(clean_str(track.primary_artist))
            queries.append(track.primary_artist)

        if track.primary_artist and track.title:
            queries.append(f'{clean_str(track.primary_artist)} {clean_str(track.title)}')
            queries.append(f'{clean_str(track.title)} {clean_str(track.primary_artist)}')
            queries.append(f'{clean_str(track.primary_artist)} - {clean_str(track.title)}')
            queries.append(f'{clean_str(track.title)} - {clean_str(track.primary_artist)}')
            queries.append(f'{track.primary_artist} {track.title}')
            queries.append(f'{track.title} {track.primary_artist}')
            queries.append(f'{track.primary_artist} - {track.title}')

        if track.album_name:
            queries.append(track.album_name)

        return await self.__search_with_queries(
            query_attempts=queries,
            reference_track=track
        )
    
    async def __search_on_origin_service(self, track: Track) -> Optional[Track]:
        """
        If it is suspected that the track originates from the same service, it tries to fetch it directly.

        :param track: The track to search for.
        :return: The matched track,
        """

        if (track.service_name and self._target.service_name) and (track.service_name == self._target.service_name):
            maybe_match = await self._target.get_track(track.service_id)
            
            if maybe_match and track.matches(maybe_match):
                return maybe_match
            
        return None
    
    async def __search_by_isrc_only(self, track: Track) -> Optional[Track]:
        """
        If supported by the target service, this tries to search for a track using its ISRC.

        In theory, this should be the most reliable way to match tracks.

        :param track: The track to search for.
        :return: The matched track,
        """

        if not track.isrc or not self._target.supports_direct_isrc_querying:
            return None
        
        try:
            likely_match = await self._target.get_track_by_isrc(
                isrc=track.isrc
            )

            if likely_match and track.matches(likely_match):
                return likely_match
        except TrackNotFoundException as e:
            pass

        return None