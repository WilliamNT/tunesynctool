from dataclasses import replace
from typing import List, Optional

from thefuzz import fuzz

from ..normalizer import normalize_str
from ..tokenizer import tokenize, GenericTokenType
from ..classifier import group_tokens
from ..classifier.types import SemanticGroup, SemanticType
from ..classifier.constants import (
    RECORDING_VERSION_KEYWORDS,
    COSMETIC_KEYWORDS,
    TIER_KEYWORDS,
    FEATURE_KEYWORDS,
    FEATURE_KEYWORDS_GATED,
)
from tunesynctool.models import Track

"""
Region-based track similarity.

The scorer works off the classifier's SemanticGroups instead of the raw title.
The core (TITLE) is what has to match, and the non-core regions carry evidence
about whether two tracks are the same recording or just different takes of the
same work. That evidence is weighed in rather than bolted on: a version marker
mismatch (original vs remix, remix vs live) demotes the score through a graded
version component instead of a flat penalty, and the names in a contribution
marker are cross-checked against the other track's artists in both directions,
so '(feat. Ariana Grande)' agrees with a candidate that actually lists Ariana
Grande and disagrees with the solo cut.

Which field a piece of metadata landed in is not trusted on its own. A messy
file writes the artist into the title ('Artist - Title' rips), files the title
under the artist and the artist under the title, or leaves the artist blank
entirely, and in every one of those the two names are still both present. So the
artist is looked for wherever it actually is: a swapped pair of tags is put back
the right way round before anything is scored, an artist name sitting in a title
is taken out of the core before the cores are compared, and an artist that is
missing from its own field but written into the other track's title is credited
as present rather than counted as absent.

The core is compared two ways and the better one wins. The chunked-ordered way
splits one core into ordered word chunks and matches each to the next
close-enough word of the other core, keeping the chunks in order; it is
symmetric so a short core does not score 1.0 against a long one. The per-word
match is a Damerau-Levenshtein (OSA) ratio, so a single adjacent transposition
('Recrod' vs 'Record') still crosses the threshold. The fuzzy way (token-sorted
ratio) is order-insensitive and rescues typos and reordered words.

Two hard gates stop the weighted average from inflating a non-match: a core below
the title floor caps the whole score, and a duration that is way off caps it too.
Metadata agreement alone should not float a wrong-title or wrong-length
candidate to a high score.
"""

_TITLE_WEIGHT = 4.0
_ARTIST_WEIGHT = 3.0
_CONTRIBUTION_WEIGHT = 1.0
_VERSION_WEIGHT = 2.5
_ALBUM_WEIGHT = 1.25
_DURATION_WEIGHT = 0.75
_TRACK_NUMBER_WEIGHT = 0.5
_RELEASE_YEAR_WEIGHT = 0.5

# a recording-kind mismatch where one side is plain and the other carries a
# version ('Save Your Tears' vs 'Save Your Tears (Remix)') scores this on the
# version component: demoted but not rejected, the 'better than nothing' case. It
# sits above the fuzzy ratio of two clearly different kinds ('Remix' vs 'Live'),
# so the ladder is monotone: same kind (1.0) > named-remixer difference > plain
# vs versioned > two different kinds.
#
# The demote is mild across the board. To a user a live, acoustic, remix or bare
# 'version' take is the same song in different paint, and the matcher's ranker
# keeps the highest-scoring candidate, so a plain original (1.0) outranks a
# versioned take (this) and the version only wins when nothing closer is on the
# target service. The cosmetic words (remaster, mono, stereo, edit) are already
# stripped by the classifier before this runs, so what reaches here is a genuine
# version marker.
_VERSION_ONE_SIDED = 0.85

# how close a chunk (one core word) has to be to a candidate word to count as the
# same word, keeping the chunked-ordered match tolerant of typos
_CHUNK_MATCH_THRESHOLD = 0.8

# duration is a trustable field: full credit within the tolerance band, then a
# linear decay to zero at the full-decay point, then nothing. Past the gate a
# way-off duration caps the whole score regardless of the other fields.
_DURATION_TOLERANCE = 10
_DURATION_FULL_DECAY = 30
_DURATION_GATE = 60
_CAP_DURATION = 0.5

# a core this far below a perfect match is almost certainly a different track, so
# the weighted average (which can still be dragged up by artist/album/duration)
# is capped no matter how well the rest agrees.
_TITLE_FLOOR = 0.5
_CAP_TITLE_FLOOR = 0.5

# a near-perfect title core with a clearly different artist is the signature of a
# cover or a namesake — a different recording that shares the title, not the same
# track mis-tagged. A mis-tag keeps the artist or drops it (the placeholder case
# is handled in _artist_score), it does not swap in a real but unrelated one. The
# perfect title can still drag the weighted average over the floor, so the artist
# caps it, the same way the title floor caps a barely-matching core.
#
# The gate measures artist coverage, not the token-sort ratio the weighted average
# uses: a shared-token cover ("John Doe" vs "John Smith") and a truncation ("The
# Weeknd" vs "The") both sit near 0.5 on token-sort and no single floor separates
# them. Coverage of the shorter side's tokens does — a truncation leaves every
# short token matched (1.0) while a cover always has a token that matches nothing
# (0.5 or below).
_ARTIST_TOKEN_MATCH = 0.6
_ARTIST_FLOOR = 0.7
_TITLE_NEAR_PERFECT = 0.99
_CAP_ARTIST = 0.5

# how strongly the crossed reading of a candidate's tags has to agree before the
# title and the artist are swapped back. Both crossed pairs have to clear it, so
# a candidate that merely has a different title is never rewritten; only a
# genuine tagger mix-up, where each string matches the other field, is.
_SWAP_CONFIDENCE = 0.8

# what an artist found in the other track's title is worth. The name is written
# out in full there, so it is present evidence, not missing evidence: 'The
# Birthday Massacre - Superstition' with a blank artist field carries its artist
# just as plainly as the field would have. Full agreement, the same as a
# matching field.
_RECOVERED_ARTIST = 1.0

# artist strings that mean "no idea who the artist is" rather than a real credit,
# so they are weighed as missing evidence (no artist weight) instead of a wrong
# artist. A track mis-tagged as "Various Artists" is the same recording, not a
# different one, and a placeholder must not trip the artist gate below.
_ARTIST_PLACEHOLDER_NAMES = {"various artists", "va", "various", "unknown artist"}

# release years are unreliable across reissues (a 1978 track remastered in 2022),
# so the band is generous: full credit within two years, decay to zero at fifteen.
_YEAR_TOLERANCE = 2
_YEAR_FULL_DECAY = 15

# how tight a fuzzy match a contribution name needs against an artist string to
# count as 'this contributor is one of that track's artists'
_NAME_MATCH_THRESHOLD = 80

# words dropped from a contribution region before the rest are treated as
# contributor names: every classifier keyword (so 'remix', 'feat', 'with',
# 'bonus' all go) plus the joiners that only glue names together. The bare 'w'
# is the feature-slash opener, kept out for the same reason as 'feat'.
_JOINER_WORDS = {'vs', 'and', 'n', 'w'}
_CONTRIBUTION_DROP_WORDS = (
    RECORDING_VERSION_KEYWORDS
    | COSMETIC_KEYWORDS
    | TIER_KEYWORDS
    | FEATURE_KEYWORDS
    | FEATURE_KEYWORDS_GATED
    | _JOINER_WORDS
)


def track_score(source: Track, candidate: Optional[Track]) -> float:
    """Approximate how close two tracks are, region by region.

    ISRC or MusicBrainz ID agreement short-circuits to 1.0: the same recording is
    the same recording. Otherwise a candidate whose title and artist tags are
    swapped is put back the right way round first, so the rest of the scoring
    reads the fields it expects. Then the core title, the contribution/artist
    agreement and the version-region similarity are always weighed together; the
    primary artist is weighed when the candidate carries it (a missing source
    artist is no evidence, not a penalty); and the album, duration, track number
    and release year are added when both sides carry them. Two hard gates then cap
    a core that barely matches or a duration that is way off.

    :param source: The track to match from.
    :param candidate: The track to match against, or None.
    :return: A similarity between 0.0 and 1.0.
    """

    if not candidate:
        return 0.0

    if source.isrc and candidate.isrc and source.isrc == candidate.isrc:
        return 1.0

    if source.musicbrainz_id and candidate.musicbrainz_id and source.musicbrainz_id == candidate.musicbrainz_id:
        return 1.0

    candidate = _repair_swapped_fields(source, candidate)

    source_regions = _semantic_regions(source)
    candidate_regions = _semantic_regions(candidate)

    title = _title_score(source, candidate, source_regions, candidate_regions)

    weight = _TITLE_WEIGHT + _CONTRIBUTION_WEIGHT + _VERSION_WEIGHT
    weighted = title * _TITLE_WEIGHT
    artist = _artist_score(source, candidate)

    if artist is not None:
        weighted += artist * _ARTIST_WEIGHT
        weight += _ARTIST_WEIGHT

    weighted += _contribution_score(source, candidate, source_regions, candidate_regions) * _CONTRIBUTION_WEIGHT
    weighted += _version_score(source_regions, candidate_regions) * _VERSION_WEIGHT

    if source.album_name and candidate.album_name:
        weighted += _string_similarity(source.album_name, candidate.album_name) * _ALBUM_WEIGHT
        weight += _ALBUM_WEIGHT

    if source.duration_seconds and candidate.duration_seconds:
        weighted += _duration_score(source.duration_seconds, candidate.duration_seconds) * _DURATION_WEIGHT
        weight += _DURATION_WEIGHT

    if source.track_number and candidate.track_number:
        weighted += _track_number_score(source.track_number, candidate.track_number) * _TRACK_NUMBER_WEIGHT
        weight += _TRACK_NUMBER_WEIGHT

    if source.release_year and candidate.release_year:
        weighted += _year_score(source.release_year, candidate.release_year) * _RELEASE_YEAR_WEIGHT
        weight += _RELEASE_YEAR_WEIGHT

    score = weighted / weight if weight else 0.0

    if title < _TITLE_FLOOR:
        score = min(score, _CAP_TITLE_FLOOR)

    # The artist gate only fires when both sides carry a real, non-placeholder
    # artist — a missing or placeholder artist is no evidence (handled above),
    # not a different artist. It then caps a near-perfect title whose artist is
    # clearly different, which is the cover/namesake signature.
    if (title >= _TITLE_NEAR_PERFECT
            and _both_artists_real(source, candidate)
            and _artist_coverage(source, candidate) < _ARTIST_FLOOR):
        score = min(score, _CAP_ARTIST)

    if _duration_exceeds_gate(source, candidate):
        score = min(score, _CAP_DURATION)

    return round(score, 2)

def _repair_swapped_fields(source: Track, candidate: Track) -> Track:
    """Puts a candidate's title and artist back the right way round when they were tagged the wrong way.

    A tagger that files the title under the artist and the artist under the title
    loses nothing: both strings are still there, just crossed. The crossed
    reading is taken only when each of its two pairs agrees strongly and the
    whole crossed reading beats the straight one, so a candidate that simply has
    a different title is never rewritten. Both pairs have to agree because one
    alone is what an ordinary near-match already looks like.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :return: The candidate, or a copy with its title and artist exchanged.
    """

    if not (source.title and source.primary_artist and candidate.title and candidate.primary_artist):
        return candidate

    straight = min(
        _string_similarity(source.title, candidate.title),
        _string_similarity(source.primary_artist, candidate.primary_artist),
    )
    crossed = min(
        _string_similarity(source.title, candidate.primary_artist),
        _string_similarity(source.primary_artist, candidate.title),
    )

    if crossed <= _SWAP_CONFIDENCE or crossed <= straight:
        return candidate

    return replace(candidate, title=candidate.primary_artist, primary_artist=candidate.title)

def _semantic_regions(track: Track) -> List[SemanticGroup]:
    """Classify a track's title into regions, using its own artists for the leaked-artist fallback."""

    artists: List[str] = []
    if track.primary_artist:
        artists.append(track.primary_artist)

    artists.extend(track.additional_artists or [])

    return group_tokens(tokenize(normalize_str(track.title or '')), artists=artists or None)

def _title_core_text(regions: List[SemanticGroup]) -> str:
    """The joined TITLE fragments of a track, lowercased and whitespace-collapsed for matching."""

    text = ' '.join(str(g) for g in regions if g.semantic_type == SemanticType.TITLE)
    return ' '.join(text.split()).lower()

def _damerau_levenshtein_osa(a: str, b: str) -> int:
    """Damerau-Levenshtein (optimal string alignment) distance between two words.

    Like Levenshtein but an adjacent transposition costs one edit, so 'reocrd'
    is one step from 'record' instead of two. OSA is the bounded-memory variant:
    no substring edits, which is all a single-word typo ever needs.

    :param a: One word.
    :param b: The other word.
    :return: The edit distance.
    """

    la, lb = len(a), len(b)
    previous = list(range(lb + 1))
    two_above = None

    for i in range(1, la + 1):
        current = [i] + [0] * lb

        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)

            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                current[j] = min(current[j], two_above[j - 2] + 1)

        two_above = previous
        previous = current

    return previous[lb]

def _damerau_levenshtein_similarity(a: str, b: str) -> float:
    """Damerau-Levenshtein similarity of two words as a 0.0-1.0 ratio."""

    if not a and not b:
        return 1.0
    
    if not a or not b:
        return 0.0
    
    return 1.0 - _damerau_levenshtein_osa(a, b) / max(len(a), len(b))

def _ordered_token_coverage(needle: str, haystack: str) -> float:
    """How much of needle is covered, in order, by words of haystack.

    Each needle word is matched to the next close-enough haystack word after the
    cursor, so the chunks keep their order; a Damerau-Levenshtein ratio lets a
    chunk match a near-equal word (including a transposed typo) instead of
    demanding exact equality.

    :param needle: The chunked string, split into ordered words.
    :param haystack: The intact string the chunks are matched against.
    :return: The covered character fraction of needle, between 0.0 and 1.0.
    """

    needle_words = needle.split()

    if not needle_words:
        return 1.0
    
    haystack_words = haystack.split()

    total = sum(len(w) for w in needle_words)
    cursor = -1
    covered = 0

    for w in needle_words:
        best_index = -1
        best_ratio = 0.0

        for i, h in enumerate(haystack_words):
            if i <= cursor:
                continue

            ratio = _damerau_levenshtein_similarity(w, h)

            if ratio > best_ratio:
                best_ratio = ratio
                best_index = i

        if best_index >= 0 and best_ratio >= _CHUNK_MATCH_THRESHOLD:
            cursor = best_index
            covered += len(w) * best_ratio

    return covered / total

def _chunked_ordered_similarity(a: str, b: str) -> float:
    """The symmetric chunked-ordered similarity: both directions must cover, so a short core does not score 1.0 against a long one."""

    return min(_ordered_token_coverage(a, b), _ordered_token_coverage(b, a))

def _string_similarity(a: str, b: str) -> float:
    """Token-sorted fuzzy ratio, order-insensitive, length-aware and case-insensitive so casing never skews the score."""

    return fuzz.token_sort_ratio((a or '').lower(), (b or '').lower()) / 100

def _core_similarity(a: str, b: str) -> float:
    """The better of the chunked-ordered and the token-sorted readings of two cores."""

    return max(_chunked_ordered_similarity(a, b), _string_similarity(a, b))

def _title_score(source: Track, candidate: Track, source_regions: List[SemanticGroup], candidate_regions: List[SemanticGroup]) -> float:
    """Compares the two cores by the better of the chunked-ordered and the fuzzy ratio.

    A core that still carries an artist name is compared a second time with that
    name taken out, and the better reading wins. The classifier only gets to type
    a region it can see the edges of — a bracket, a trailing dash-suffix, a
    feature opener — so the plain 'Artist - Title' of a ripped filename splits
    into two title fragments and the artist stays in the core, where it drags the
    comparison down. Both tracks' artists are stripped from both cores, since the
    side that lost its artist field is exactly the side that cannot recognise its
    own name.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :param source_regions: The classified regions of the source title.
    :param candidate_regions: The classified regions of the candidate title.
    :return: Core similarity between 0.0 and 1.0.
    """

    source_core = _title_core_text(source_regions)
    candidate_core = _title_core_text(candidate_regions)

    if not source_core and not candidate_core:
        return 1.0

    if not source_core or not candidate_core:
        return 0.0

    score = _core_similarity(source_core, candidate_core)

    # already as good as it gets; nothing a strip could add
    if score >= _TITLE_NEAR_PERFECT:
        return score

    runs = _artist_word_runs(source, candidate)
    stripped_source = _strip_artist_names(source_core, runs)
    stripped_candidate = _strip_artist_names(candidate_core, runs)

    if stripped_source == source_core and stripped_candidate == candidate_core:
        return score

    return max(score, _core_similarity(stripped_source, stripped_candidate))

def _artist_score(source: Track, candidate: Track) -> Optional[float]:
    """Primary-artist agreement, or None when there is no artist evidence to weigh.

    The source is the user's file and the candidate is a real service result, so
    the two missing-artist cases are not symmetric. A source with no artist is
    just a poorly tagged file: no evidence, so None drops the artist weight and
    the field neither helps nor hurts. A candidate with no artist is a red flag,
    since real services populate it, so that returns 0.0 and still counts. A
    placeholder credit ("Various Artists" and the like) on either side is no
    evidence either — a compilation mis-tag is the same recording, and it must not
    be scored as a wrong artist or trip the artist gate.

    Before any of that is believed, the artist is looked for in the other track's
    title. A field that is blank, a placeholder or plain wrong is no reason to
    call the artist absent when the name is written out in the other title, so
    that case is credited instead of penalised.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :return: Artist agreement between 0.0 and 1.0, or None to skip the field.
    """

    s = source.primary_artist or ''
    c = candidate.primary_artist or ''

    if not s or s.lower() in _ARTIST_PLACEHOLDER_NAMES:
        return _RECOVERED_ARTIST if _artist_in_title(c, source.title) else None

    if not c:
        return _RECOVERED_ARTIST if _artist_in_title(s, candidate.title) else 0.0

    if c.lower() in _ARTIST_PLACEHOLDER_NAMES:
        return _RECOVERED_ARTIST if _artist_in_title(s, candidate.title) else None

    ratio = fuzz.token_sort_ratio(s.lower(), c.lower()) / 100

    if ratio < _RECOVERED_ARTIST and (_artist_in_title(s, candidate.title) or _artist_in_title(c, source.title)):
        return _RECOVERED_ARTIST

    return ratio

def _artist_tokens(name: str) -> List[str]:
    """A primary-artist string split into lowercase alphanumeric words.

    Tokenized rather than split on a character class, so the words survive every
    script. An ascii-only class empties a Japanese or Cyrillic name altogether,
    which reads downstream as "this side has no artist tokens" instead of "this
    is a different artist", and it cuts an accented latin name in half ("Björk"
    into "bj" and "rk"), which reads as a different artist from "Bjork".

    :param name: The artist name to split.
    :return: The lowercased alphanumeric words, in order.
    """

    return [tok.value.lower() for tok in tokenize(normalize_str(name or '')) if tok.type == GenericTokenType.ALPHANUMERIC]

def _artist_in_title(name: str, title: Optional[str]) -> bool:
    """Whether an artist name appears in a title as a contiguous run of its words.

    Matched whole-name, the same way the classifier's leaked-artist fallback
    matches, so a one-word artist never trips on an unrelated title word.

    :param name: The artist name to look for.
    :param title: The title to look in.
    :return: True if the whole name is present.
    """

    run = _artist_tokens(name)

    if not run:
        return False

    words = _artist_tokens(title or '')

    return any(words[i:i + len(run)] == run for i in range(len(words) - len(run) + 1))

def _artist_word_runs(source: Track, candidate: Track) -> List[List[str]]:
    """Both tracks' artist names as word runs, longest first.

    Longest first so a name is taken out whole before a shorter one that overlaps
    it could nibble a word off the front.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :return: The non-empty word runs, longest first.
    """

    runs = [_artist_tokens(name) for name in _artist_strings(source) + _artist_strings(candidate)]

    return sorted((run for run in runs if run), key=len, reverse=True)

def _strip_artist_names(core: str, runs: List[List[str]]) -> str:
    """Drops whole artist names out of a title core, keeping the rest in order.

    A run that would empty the core is left in place: a self-titled track ("Bad
    Company" by Bad Company) has to keep its name, the same never-empty-core rule
    the classifier follows.

    :param core: The title core to strip.
    :param runs: The artist word runs to drop, longest first.
    :return: The core without the artist names.
    """

    words = core.split()

    for run in runs:
        if len(run) > len(words):
            continue

        kept: List[str] = []
        index = 0

        while index < len(words):
            if words[index:index + len(run)] == run:
                index += len(run)
                continue

            kept.append(words[index])
            index += 1

        if kept:
            words = kept

    return ' '.join(words)

def _both_artists_real(source: Track, candidate: Track) -> bool:
    """Whether source and candidate both carry a real, non-placeholder artist."""

    s = (source.primary_artist or '').lower()
    c = (candidate.primary_artist or '').lower()

    return bool(s and c and s not in _ARTIST_PLACEHOLDER_NAMES and c not in _ARTIST_PLACEHOLDER_NAMES)

def _artist_coverage(source: Track, candidate: Track) -> float:
    """Fraction of the shorter side's artist tokens matched by a token on the longer side.

    A truncation or a single-token typo leaves the shorter side's tokens all
    recognisable on the longer side, so coverage is 1.0. A different artist that
    shares a token (a cover or a namesake) always has a token that matches nothing,
    so coverage drops to 0.5 or below — the signal the artist gate uses to tell a
    cover from a mis-tag, which the token-sort ratio cannot.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :return: Coverage between 0.0 and 1.0.
    """

    st = _artist_tokens(source.primary_artist)
    ct = _artist_tokens(candidate.primary_artist)

    if not st and not ct:
        return 1.0

    if not st or not ct:
        return 0.0

    small, large = (st, ct) if len(st) <= len(ct) else (ct, st)
    matched = sum(1 for n in small if any(_damerau_levenshtein_similarity(n, h) >= _ARTIST_TOKEN_MATCH for h in large))

    return matched / len(small)

def _contribution_names(regions: List[SemanticGroup]) -> List[str]:
    """The contributor name phrases carried by a track's CONTRIBUTION_MARKER regions.

    A contribution region is split on its joiners (comma, slash, ampersand, the
    word 'vs') into name phrases, every classifier keyword and joiner word is
    dropped, and the surviving words of each phrase are joined back into a name.
    So '(feat. Ariana Grande & Flo Rida)' yields ['ariana grande', 'flo rida']
    and '(Benny Benassi vs. MazZz Remix)' yields ['benny benassi', 'mazzz'].

    :param regions: The classified regions of a track's title.
    :return: Lowercased contributor name phrases, in order.
    """

    phrases: List[List] = []
    for g in regions:
        if g.semantic_type != SemanticType.CONTRIBUTION_MARKER:
            continue

        current: List = []
        for tok in g.tokens:
            if tok.type in (GenericTokenType.COMMA, GenericTokenType.SLASH, GenericTokenType.AMPERSAND):
                phrases.append(current)
                current = []
                continue

            if tok.type == GenericTokenType.ALPHANUMERIC and tok.value.lower() == 'vs':
                phrases.append(current)
                current = []
                continue

            current.append(tok)

        phrases.append(current)

    names: List[str] = []
    for toks in phrases:
        words = [
            tok.value.lower()
            for tok in toks
            if tok.type == GenericTokenType.ALPHANUMERIC and tok.value.lower() not in _CONTRIBUTION_DROP_WORDS
        ]

        if words:
            names.append(' '.join(words))

    return names

def _artist_strings(track: Track) -> List[str]:
    """The primary and additional artists of a track, lowercased, as whole strings for name matching."""

    strings = [track.primary_artist] + list(track.additional_artists or [])
    return [s.lower() for s in strings if s]

def _name_in_artists(needle: str, haystacks: List[str]) -> bool:
    """Whether a contributor name phrase fuzzy-matches any of a track's artist strings."""

    if not needle:
        return True
    
    for h in haystacks:
        if fuzz.token_sort_ratio(needle, h) >= _NAME_MATCH_THRESHOLD:
            return True
        
    return False

def _contribution_score(source: Track, candidate: Track, source_regions: List[SemanticGroup], candidate_regions: List[SemanticGroup]) -> float:
    """Cross-check contribution names against artists in both directions.

    Direction one asks whether the source's contributors are among the
    candidate's artists; direction two asks the reverse. A side with no
    contributors contributes nothing to check, which scores 1.0 on that
    direction, so a plain candidate against a featured source is only graded on
    the featured direction. Neither side carrying contributors is a neutral 1.0,
    so the component never penalises a clean pair.

    :param source: The track to match from.
    :param candidate: The track to match against.
    :param source_regions: The classified regions of the source title.
    :param candidate_regions: The classified regions of the candidate title.
    :return: Agreement between 0.0 and 1.0.
    """

    source_names = _contribution_names(source_regions)
    candidate_names = _contribution_names(candidate_regions)

    if not source_names and not candidate_names:
        return 1.0

    source_artists = _artist_strings(source)
    candidate_artists = _artist_strings(candidate)

    forward = _matched_names_fraction(source_names, candidate_artists)
    reverse = _matched_names_fraction(candidate_names, source_artists)

    return (forward + reverse) / 2

def _matched_names_fraction(needles: List[str], haystacks: List[str]) -> float:
    """The fraction of contributor names found among a track's artist strings."""

    if not needles:
        return 1.0
    
    found = sum(1 for name in needles if _name_in_artists(name, haystacks))

    return found / len(needles)

def _version_text(regions: List[SemanticGroup]) -> str:
    """The joined VERSION_MARKER fragments of a track, lowercased and whitespace-collapsed for matching."""

    text = ' '.join(str(g) for g in regions if g.semantic_type == SemanticType.VERSION_MARKER)
    return ' '.join(text.split()).lower()

def _version_score(source_regions: List[SemanticGroup], candidate_regions: List[SemanticGroup]) -> float:
    """Graded similarity of the two version regions.

    Both empty is a neutral 1.0, no version evidence either way. One side
    carrying a version and the other not (plain vs remix) scores the one-sided
    constant, the demoted-but-not-rejected 'better than nothing' case. Two
    non-empty version texts are compared by token-sorted ratio, so the same
    recording kind stays at 1.0 and a different one lands between the one-sided
    constant and 1.0 by how far apart the labels are.

    :param source_regions: The classified regions of the source title.
    :param candidate_regions: The classified regions of the candidate title.
    :return: Version-region similarity between 0.0 and 1.0.
    """

    source_version = _version_text(source_regions)
    candidate_version = _version_text(candidate_regions)

    if not source_version and not candidate_version:
        return 1.0

    if not source_version or not candidate_version:
        return _VERSION_ONE_SIDED

    return _string_similarity(source_version, candidate_version)

def _duration_score(a: int, b: int) -> float:
    """Duration closeness with a tolerance band and a linear decay.

    Full credit within the tolerance band, then a straight decay to zero at the
    full-decay point, then nothing. A track twice as long is not 'half close'.

    :param a: One duration in seconds.
    :param b: The other duration in seconds.
    :return: Closeness between 0.0 and 1.0.
    """

    diff = abs(a - b)
    if diff <= _DURATION_TOLERANCE:
        return 1.0
    
    if diff <= _DURATION_FULL_DECAY:
        return 1.0 - (diff - _DURATION_TOLERANCE) / (_DURATION_FULL_DECAY - _DURATION_TOLERANCE)

    return 0.0

def _duration_exceeds_gate(source: Track, candidate: Track) -> bool:
    """Whether both durations are present and far enough apart to trip the hard gate."""

    if not source.duration_seconds or not candidate.duration_seconds:
        return False
    
    return abs(source.duration_seconds - candidate.duration_seconds) > _DURATION_GATE

def _track_number_score(a: int, b: int) -> float:
    """Track-number closeness: an exact slot match is full credit, anything else nothing."""

    return 1.0 if a == b else 0.0

def _year_score(a: int, b: int) -> float:
    """Release-year closeness with a generous band for reissues and remasters.

    Full credit within the tolerance, then a straight decay to zero at the
    full-decay point. A remaster decades later is the same recording, so the band
    is wide on purpose and the weight small.

    :param a: One release year.
    :param b: The other release year.
    :return: Closeness between 0.0 and 1.0.
    """

    diff = abs(a - b)
    
    if diff <= _YEAR_TOLERANCE:
        return 1.0
    
    if diff <= _YEAR_FULL_DECAY:
        return 1.0 - (diff - _YEAR_TOLERANCE) / (_YEAR_FULL_DECAY - _YEAR_TOLERANCE)

    return 0.0