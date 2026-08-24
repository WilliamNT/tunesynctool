from typing import List, Optional

from ..tokenizer import GenericToken, GenericTokenType, tokenize
from ..normalizer import normalize_str
from .types import SemanticGroup, SemanticType
from .constants import (
    RECORDING_VERSION_KEYWORDS, COSMETIC_KEYWORDS, TIER_KEYWORDS,
    FEATURE_KEYWORDS, FEATURE_KEYWORDS_GATED, FEATURE_SLASH,
)

"""
Splits a normalized, tokenized title into semantic regions.

group_tokens walks the token stream and emits one SemanticGroup per structural
piece: the leading title, each bracketed clause, each trailing dash-suffix and
the separators between them. Each non-title region is then typed by content in
_classify_region, following the rules spelled out in types.py.
"""

_OPEN = {GenericTokenType.LPAREN}
_CLOSE = {GenericTokenType.RPAREN}

# depth-zero separators that split the leading title into fragments
_SEPARATORS = {
    GenericTokenType.DASH, GenericTokenType.SLASH, GenericTokenType.COMMA,
    GenericTokenType.AMPERSAND, GenericTokenType.PLUS, GenericTokenType.SEMICOLON,
}

# a trailing dash is a suffix only when its tail carries one of these; without
# it 'Love - Hate' is an in-title dash and both sides stay TITLE
_SUFFIX_KEYWORDS = RECORDING_VERSION_KEYWORDS | COSMETIC_KEYWORDS | TIER_KEYWORDS

# all keyword sets folded together, so a capitalized keyword never counts as a
# name token when weighing the 'Name + Keyword' shape
_ALL_KEYWORDS = (
    RECORDING_VERSION_KEYWORDS | COSMETIC_KEYWORDS | TIER_KEYWORDS
    | FEATURE_KEYWORDS | FEATURE_KEYWORDS_GATED
)

# keywords that credit a person when a Capitalized name precedes them; packaging
# and source markers and pure recording types do not, so 'Name Remaster' or
# 'Name Live' stays a version instead of a contribution
_REMIXER_KEYWORDS = {
    'remix', 'cover', 'edit', 'mix', 'dub', 'vip', 'club', 'bootleg',
    'nightcore', 'rerecorded', 'recorded', 'version',
}


def _is_spaced_dash(tokens: List[GenericToken], index: int) -> bool:
    """Whether the dash at the index has a space on either side, marking it structural rather than part of a word like 'Re-Recorded'."""

    if tokens[index].type != GenericTokenType.DASH:
        return False

    before = index > 0 and tokens[index - 1].type == GenericTokenType.SPACE
    after = index + 1 < len(tokens) and tokens[index + 1].type == GenericTokenType.SPACE

    return before or after

def _is_feature_start(tokens: List[GenericToken], index: int) -> bool:
    """Whether the token at the index opens a feature region: a bare feature word or the 'w/' pair."""

    tok = tokens[index]
    
    if tok.type != GenericTokenType.ALPHANUMERIC:
        return False
    
    if tok.value.lower() in FEATURE_KEYWORDS:
        return True

    return tok.value.lower() == FEATURE_SLASH and index + 1 < len(tokens) and tokens[index + 1].type == GenericTokenType.SLASH

def _tail_is_suffix(tokens: List[GenericToken], dash_index: int) -> bool:
    """
    Whether a spaced dash opens a trailing suffix.

    The tail must carry a version, cosmetic or tier keyword at depth zero. A
    keyword inside a bracket belongs to that bracket's own version tag, so
    'Hate (Original Mix)' does not count and 'Hate' stays the title; a keyword
    after a closed bracket, as in 'Skore (BR) Remix', spans it and marks the
    whole tail a suffix.

    :param tokens: The full token stream.
    :param dash_index: The index of the dash to test.
    :return: True if the dash opens a trailing suffix region.
    """

    i = dash_index + 1
    depth = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok.type in _OPEN:
            depth += 1

        elif tok.type in _CLOSE:
            if depth == 0:
                break

            depth -= 1

        elif depth == 0:
            if tok.type == GenericTokenType.DASH and _is_spaced_dash(tokens, i):
                break

            if tok.type == GenericTokenType.ALPHANUMERIC and tok.value.lower() in _SUFFIX_KEYWORDS:
                return True
            
        i += 1

    return False

def _trim_spaces(tokens: List[GenericToken]) -> List[GenericToken]:
    """Drops leading and trailing space tokens from a region."""

    start = 0
    end = len(tokens)

    while start < end and tokens[start].type == GenericTokenType.SPACE:
        start += 1

    while end > start and tokens[end - 1].type == GenericTokenType.SPACE:
        end -= 1

    return tokens[start:end]

def group_tokens(
    token_sequence: List[GenericToken],
    artists: Optional[List[str]] = None,
) -> List[SemanticGroup]:
    """
    Splits a token stream into semantic regions and types each one.

    :param token_sequence: The normalized, tokenized title to group.
    :param artists: Artist names for the leaked-artist fallback; a region that
        contains one is typed as a contribution even with no keyword or opener.
    :return: The semantic groups in order, with at least one typed TITLE.
    """

    groups: List[SemanticGroup] = []
    index = 0

    def _emit(tokens: List[GenericToken], semantic_type: SemanticType) -> None:
        tokens = _trim_spaces(tokens)
        if not tokens:
            return
        groups.append(SemanticGroup(tokens=tokens, semantic_type=semantic_type))

    while index < len(token_sequence):
        tok = token_sequence[index]

        if tok.type in _OPEN:
            _emit([tok], SemanticType.SEPARATOR)
            index += 1
            region: List[GenericToken] = []
            depth = 1
            while index < len(token_sequence) and depth > 0:
                inner = token_sequence[index]

                if inner.type in _OPEN:
                    depth += 1
                    region.append(inner)
                elif inner.type in _CLOSE:
                    depth -= 1
                    if depth == 0:
                        break
                    region.append(inner)
                else:
                    region.append(inner)

                index += 1

            _emit(region, _classify_region(region, artists))

            if index < len(token_sequence) and token_sequence[index].type in _CLOSE:
                _emit([token_sequence[index]], SemanticType.SEPARATOR)
                index += 1

            continue

        # trailing dash-suffix whose tail carries a keyword; inner separators
        # stay with it so a whole credit like 'Benny Benassi vs. X & Y Remix'
        # is one region
        if tok.type == GenericTokenType.DASH and _is_spaced_dash(token_sequence, index) and _tail_is_suffix(token_sequence, index):
            _emit([tok], SemanticType.SEPARATOR)
            index += 1
            region = []
            depth = 0

            while index < len(token_sequence):
                inner = token_sequence[index]

                if depth == 0 and inner.type == GenericTokenType.DASH and _is_spaced_dash(token_sequence, index):
                    break
                if inner.type in _OPEN:
                    depth += 1
                elif inner.type in _CLOSE:
                    if depth == 0:
                        break

                    depth -= 1

                region.append(inner)
                index += 1
                
            _emit(region, _classify_region(region, artists))
            continue

        # depth-zero feature opener, split off from the leading title
        if _is_feature_start(token_sequence, index):
            region = [tok]
            index += 1

            while index < len(token_sequence):
                inner = token_sequence[index]
                if inner.type in _OPEN:
                    break

                if inner.type == GenericTokenType.DASH and _is_spaced_dash(token_sequence, index):
                    break

                region.append(inner)
                index += 1
                
            _emit(region, _classify_region(region, artists))
            continue

        if tok.type in _SEPARATORS:
            _emit([tok], SemanticType.SEPARATOR)
            index += 1
            continue

        # leading title fragment; pure punctuation (a trailing '?' after a
        # bracket) has no alphanumeric token and is dropped
        fragment: List[GenericToken] = [tok]
        index += 1

        while index < len(token_sequence):
            next_tok = token_sequence[index]

            if next_tok.type in _OPEN or next_tok.type in _SEPARATORS:
                break

            if _is_feature_start(token_sequence, index):
                break

            fragment.append(next_tok)
            index += 1

        if any(t.type == GenericTokenType.ALPHANUMERIC for t in fragment):
            _emit(fragment, SemanticType.TITLE)

    _ensure_title_core(groups)

    return groups

def _is_capitalized(token: GenericToken) -> bool:
    """Whether the token starts with an uppercase letter, used to weigh name tokens."""

    head = token.value[:1]
    return head.isalpha() and head.isupper()

def _has_keyword(tokens: List[GenericToken], keywords: set) -> bool:
    """Whether any alphanumeric token's lowercased value is in the given keyword set."""

    for tok in tokens:
        if tok.type == GenericTokenType.ALPHANUMERIC and tok.value.lower() in keywords:
            return True
        
    return False

def _first_remixer_index(tokens: List[GenericToken]) -> Optional[int]:
    """The index of the first remixer-style keyword, or None."""

    for i, tok in enumerate(tokens):
        if tok.type == GenericTokenType.ALPHANUMERIC and tok.value.lower() in _REMIXER_KEYWORDS:
            return i
        
    return None

def _artist_words(artist: str) -> List[str]:
    """The lowercased alphanumeric words of an artist name, normalized and tokenized."""

    return [tok.value.lower() for tok in tokenize(normalize_str(artist)) if tok.type == GenericTokenType.ALPHANUMERIC]

def _contains_artist(tokens: List[GenericToken], artists: Optional[List[str]]) -> bool:
    """
    Whether any supplied artist name appears as a contiguous run of its words.

    Matched whole-token, so 'Calvin' alone never trips on the title word
    'Calvin'; the whole name 'Calvin Harris' has to appear.

    :param tokens: The region to search.
    :param artists: The artist names to look for.
    :return: True if any artist name is found as a contiguous subsequence.
    """

    if not artists:
        return False

    region_words = [tok.value.lower() for tok in tokens if tok.type == GenericTokenType.ALPHANUMERIC]
    if not region_words:
        return False

    for artist in artists:
        words = _artist_words(artist)
        if not words or len(words) > len(region_words):
            continue

        for i in range(len(region_words) - len(words) + 1):
            if region_words[i:i + len(words)] == words:
                return True

    return False

def _classify_region(tokens: List[GenericToken], artists: Optional[List[str]]) -> SemanticType:
    """
    Types a non-title region by content, in the order spelled out in types.py.

    Feature opener, then the 'Name + Keyword' contribution shape, then the
    leaked-artist fallback, then version over cosmetic over tier, then subtitle.

    :param tokens: The region's tokens.
    :param artists: Artist names for the leaked-artist fallback.
    :return: The semantic type for the region.
    """

    opener_index = None
    for i, tok in enumerate(tokens):
        if tok.type == GenericTokenType.ALPHANUMERIC:
            opener_index = i
            break

    if opener_index is None:
        return SemanticType.SUBTITLE

    head = tokens[opener_index].value.lower()

    # 'From ...' is a source attribution, not a contribution or a version
    if head == 'from':
        return SemanticType.SUBTITLE

    # 1. feature opener
    if head in FEATURE_KEYWORDS or head in FEATURE_KEYWORDS_GATED:
        return SemanticType.CONTRIBUTION_MARKER
    
    if head == FEATURE_SLASH and opener_index + 1 < len(tokens) and tokens[opener_index + 1].type == GenericTokenType.SLASH:
        return SemanticType.CONTRIBUTION_MARKER

    # 2. 'Name + remixer keyword' shape: >=2 capitalized name tokens before the
    # first remixer keyword
    kw_index = _first_remixer_index(tokens)
    if kw_index is not None:
        caps_before = 0
        for tok in tokens[:kw_index]:
            if tok.type == GenericTokenType.ALPHANUMERIC and _is_capitalized(tok) and tok.value.lower() not in _ALL_KEYWORDS:
                caps_before += 1
                
        if caps_before >= 2:
            return SemanticType.CONTRIBUTION_MARKER

    # 3. leaked-artist fallback
    if _contains_artist(tokens, artists):
        return SemanticType.CONTRIBUTION_MARKER

    # 4. version > cosmetic > tier
    if _has_keyword(tokens, RECORDING_VERSION_KEYWORDS):
        return SemanticType.VERSION_MARKER
    if _has_keyword(tokens, COSMETIC_KEYWORDS):
        return SemanticType.COSMETIC_MARKER
    if _has_keyword(tokens, TIER_KEYWORDS):
        return SemanticType.TIER_MARKER

    # 5. subtitle
    return SemanticType.SUBTITLE

def _ensure_title_core(groups: List[SemanticGroup]) -> None:
    """
    Reclassifies the first non-separator group as TITLE when none is titled.

    Keeps a TITLE for a marker used as the whole name, like 'Remix' or 'Intro'.

    :param groups: The groups to patch in place.
    """

    if any(g.semantic_type == SemanticType.TITLE for g in groups):
        return

    for g in groups:
        if g.semantic_type != SemanticType.SEPARATOR:
            g.semantic_type = SemanticType.TITLE
            return