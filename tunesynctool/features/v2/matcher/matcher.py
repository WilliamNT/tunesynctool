from typing import List, Optional

from .core.scorer import track_score
from tunesynctool.models import Track

"""
Candidate ranking over the scorer.

The matcher is the last stage of the pipeline: given a source track and the
candidates a driver returned, it scores each with the scorer and keeps the best.
'Best' is the highest score, and ties are broken by a ladder rather than arrival
order, so the pick is deterministic when two candidates score alike.

The ladder, most-significant first: the score itself; then the tighter duration
(a closer length is the more trustable signal); then the more complete metadata
(a track carrying more identifying fields is the safer pick); then the lexically
smallest service id, which only decides between otherwise indistinguishable
candidates and keeps the result stable across runs.
"""

# a placeholder for a missing duration so it never wins the duration tiebreak
# against a candidate that actually carries one
_DURATION_MISSING = 9999


def match_track(source: Track, candidates: Optional[List[Track]], threshold: float = 0.0) -> Optional[Track]:
    """Pick the best candidate for a source track from a candidate list.

    Every non-null candidate is scored with the scorer; those below the threshold
    are dropped, and the rest are compared by the tiebreak ladder. An empty list
    (or one with nothing above threshold) yields None.

    :param source: The track to match from.
    :param candidates: The candidate tracks a driver returned, or None.
    :param threshold: The minimum score a candidate must reach to be kept.
    :return: The best candidate, or None.
    """

    best: Optional[Track] = None
    best_key = None

    for candidate in candidates or []:
        if candidate is None:
            continue

        score = track_score(source, candidate)

        if score < threshold:
            continue

        key = (-score, _duration_diff(source, candidate), -_metadata_completeness(candidate), _identity_key(candidate))

        if best_key is None or key < best_key:
            best_key = key
            best = candidate

    return best

def _duration_diff(source: Track, candidate: Track) -> int:
    """The absolute duration gap, or a large placeholder when either side is missing."""

    if source.duration_seconds and candidate.duration_seconds:
        return abs(source.duration_seconds - candidate.duration_seconds)
    
    return _DURATION_MISSING

def _metadata_completeness(track: Track) -> int:
    """How many identifying fields a track actually carries."""

    fields = (
        track.title,
        track.album_name,
        track.primary_artist,
        track.additional_artists,
        track.duration_seconds,
        track.track_number,
        track.release_year,
        track.isrc,
        track.musicbrainz_id,
    )
    
    return sum(1 for field in fields if field)

def _identity_key(track: Track) -> str:
    """The service id of a track, falling back to an empty string for the lexical tiebreak."""

    return track.service_id or ''