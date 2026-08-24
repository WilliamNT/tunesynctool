from typing import List, Optional, Tuple
import logging

from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.exceptions import TrackNotFoundException

from .core.scorer import track_score
from .matcher import match_track
from .core.normalizer import normalize_str
from .core.tokenizer import tokenize
from .core.classifier import group_tokens
from .core.classifier.types import SemanticType
from tunesynctool.models import Track

"""
Retrieval and ranking of a track on a target service.

Fetches candidates through a short ordered strategy ladder and hands them all to
the same ranker, so the comparison logic lives in one place. The text search runs
a finite query plan, pools the results and stops early once a candidate is
confident enough; the plan is bounded so retrieval always terminates. A
MusicBrainz-ID rung is left open, since fetching the id online is a separate step
and not something to fake here.
"""

logger = logging.getLogger(__name__)

# Skip the rest of the plan once a candidate is this sure. A clean match lands at
# or near 1.0, so a candidate already this high is not getting displaced by a
# later query. Sits above the 0.96 a versioned take scores under the scorer's
# mild version demote, so a '(Remix)' candidate does not short-circuit the search
# before a plainer original the later queries might surface — the ranker keeps
# the highest-scoring candidate, so this only stops on a near-perfect match.
_STOP_CONFIDENCE = 0.97

# The floor below which nothing is returned. It has to sit above the scorer's
# title-floor and duration-gate caps (both 0.5) or a wrong-title near-miss floats
# back up to a match at 0.5, and below the 0.96 the scorer gives a one-sided
# version pair, or real matches get rejected as misses. Re-swept on the
# MusicBrainz bench with the cover gate and the mild version demote: at 0.70 V2
# recall is 79.2% at 91.5% precision (cover false-positives 3.3%); 0.75 trades
# recall back to 77.5% for precision 92.0%. 0.70 keeps the recall the fixes
# bought, which is the point for messy user libraries.
_ACCEPT_FLOOR = 0.70

# Top-N fetched per query. Pooled ranking picks the winner, so a wider net
# trades a little cost for better coverage of noisy titles.
_SEARCH_LIMIT = 10


class AsyncTrackMatcher:
    """Finds a track's counterpart on a target service.

    Depends on the real ServiceDriver interface, wrapped async, so any real
    driver slots in unchanged and a mock behind it is what the benchmarks run
    against.

    :param target_driver: The async-wrapped driver of the service to match against.
    """

    def __init__(self, target_driver: AsyncWrappedServiceDriver) -> None:
        self._target = target_driver

    async def find_match(self, track: Track) -> Optional[Track]:
        """Best-effort match of a track onto the target service.

        Tries the origin-service fetch, then a direct ISRC lookup, then the pooled
        text search. Each rung only returns a candidate that clears the floor, so
        a non-match yields None.

        :param track: The track to match.
        :return: The matched track, if one clears the floor.
        """

        matched = await self._search_on_origin_service(track)
        if matched is not None:
            return matched

        matched = await self._search_by_isrc(track)
        if matched is not None:
            return matched

        matched = await self._search_with_text(track)
        if matched is not None:
            return matched

        logger.debug(f'No match found for track {track}.')

        return None

    def _accept_above_floor(self, source: Track, candidate: Optional[Track]) -> Optional[Track]:
        """Returns the candidate if it clears the acceptance floor, else None."""

        if candidate is None:
            return None
        
        if track_score(source, candidate) >= _ACCEPT_FLOOR:
            return candidate
        
        return None

    async def _search_on_origin_service(self, track: Track) -> Optional[Track]:
        """Fetch the track straight by id when it already comes from the target service.

        A same-service, same-id fetch is the same track, so the floor is the only
        check.

        :param track: The track to search for.
        :return: The matched track, if it clears the floor.
        """

        if not (track.service_name and self._target.service_name and track.service_name == self._target.service_name):
            return None
        
        if not track.service_id:
            return None

        try:
            candidate = await self._target.get_track(track.service_id)
        except TrackNotFoundException:
            return None
        
        return self._accept_above_floor(track, candidate)

    async def _search_by_isrc(self, track: Track) -> Optional[Track]:
        """Fetch the track by ISRC when the target supports it.

        The same recording is the same recording, so an ISRC hit is definitive.

        :param track: The track to search for.
        :return: The matched track, if it clears the floor.
        """

        if not track.isrc or not self._target.supports_direct_isrc_querying:
            return None

        try:
            candidate = await self._target.get_track_by_isrc(track.isrc)
        except TrackNotFoundException:
            return None
        
        return self._accept_above_floor(track, candidate)

    async def _search_with_text(self, track: Track) -> Optional[Track]:
        """Run the query plan and rank the pooled candidates.

        After each query the pool so far is ranked, and once the best reaches the
        stop confidence the rest are skipped. When the plan is done the best of the
        full pool is returned if it clears the floor.

        :param track: The track to search for.
        :return: The matched track, if one clears the floor.
        """

        pool: List[Track] = []
        seen: set = set()

        for query in self._build_query_plan(track):
            results = await self._target.search_tracks(query=query, limit=_SEARCH_LIMIT)
            self._merge_into_pool(pool, seen, results)

            best = match_track(track, pool)
            if best is not None and track_score(track, best) >= _STOP_CONFIDENCE:
                logger.debug(f'Early exit on query "{query}" with score {track_score(track, best)}.')
                return best

        return match_track(track, pool, threshold=_ACCEPT_FLOOR)

    def _merge_into_pool(self, pool: List[Track], seen: set, results: List[Track]) -> None:
        """Appends candidates not already pooled, deduped by service identity."""

        for candidate in results or []:
            if candidate is None:
                continue

            key = self._dedup_key(candidate)
            if key in seen:
                continue

            seen.add(key)
            pool.append(candidate)

    def _dedup_key(self, track: Track) -> Tuple:
        """Identity key for a candidate; falls back to object identity without an id."""

        if track.service_id:
            return (track.service_name or '', track.service_id)
        
        return (track.service_name or '', '__obj__', id(track))

    def _build_query_plan(self, track: Track) -> List[str]:
        """The finite ordered query plan for a track, strongest first.

        The artist and the clean core title together in both orders, then the
        'artist - core' filename convention, then the core alone, then the album
        as a last resort. The clean core is the title with brackets, features and
        version markers stripped, so 'Save Your Tears (Remix)' queries
        'save your tears' and not the word 'remix'.

        :param track: The track to build queries for.
        :return: Distinct query strings in priority order.
        """

        core = self._clean_core_title(track)
        artist = (track.primary_artist or '').strip()
        album = (track.album_name or '').strip()

        queries: List[str] = []
        if artist and core:
            queries.append(f'{artist} {core}')
            queries.append(f'{core} {artist}')
            queries.append(f'{artist} - {core}')

        if core:
            queries.append(core)

        if artist and not core:
            queries.append(artist)

        if album and (core or artist):
            queries.append(album)

        return self._dedupe_queries(queries)

    def _clean_core_title(self, track: Track) -> str:
        """The clean core title of a track, lowercased and whitespace-collapsed."""

        artists: List[str] = []
        if track.primary_artist:
            artists.append(track.primary_artist)

        artists.extend(track.additional_artists or [])

        regions = group_tokens(tokenize(normalize_str(track.title or '')), artists=artists or None)
        text = ' '.join(str(g) for g in regions if g.semantic_type == SemanticType.TITLE)

        return ' '.join(text.split()).lower()

    def _dedupe_queries(self, queries: List[str]) -> List[str]:
        """Preserves order while dropping repeated query strings."""

        seen: set = set()
        out: List[str] = []
        
        for q in queries:
            if q and q not in seen:
                seen.add(q)
                out.append(q)

        return out