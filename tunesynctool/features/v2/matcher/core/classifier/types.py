from dataclasses import dataclass
from typing import List
from enum import StrEnum

from ..tokenizer import GenericToken

"""
How a title is cut into SemanticGroups.

The classifier walks the token stream left to right and splits it into regions.
The leading run before any bracket or trailing dash is the TITLE; each bracketed
clause (parentheses, brackets, braces) is its own region; a trailing dash opens
one more region from the dash to the end. Everything structural between regions
(dashes, slashes, commas, ampersands, the bracket tokens themselves) is typed
SEPARATOR and split into its own group.

Each non-title region is typed by content, in this order:

1. Opens with a feature keyword, so it is a CONTRIBUTION_MARKER. Bare feature
   words (feat, ft, featuring, prod) count anywhere at the front; gated words
   ('with') and the 'w/' pair count only as the opening token. That is what
   keeps '(Dance with Somebody)' a subtitle: 'with' is mid-phrase, not the
   opener. A region opening with 'from' is a source attribution and also stays
   a subtitle.

2. Holds a remixer keyword (remix, cover, edit, mix, dub, version, ...) with two
   or more Capitalized non-keyword tokens before it, so it is a
   CONTRIBUTION_MARKER. This is the 'Name Remix' / 'Name Cover' shape: 'Benny
   Benassi Remix' is a contribution, 'Hot Remix' is not (one Capitalized word is
   a descriptor). Packaging and source markers (remaster, edition, soundtrack,
   ...) and pure recording types (live, acoustic, ...) are not remixer credits,
   so 'Name Remaster' or 'Name Live' stays a version. Capitalization alone never
   promotes a region with no remixer keyword.

3. Any token in the supplied artist-name list is a CONTRIBUTION_MARKER, even
   with no keyword and no feature opener. This is the leaked-artist fallback:
   '(Ariana Grande)' with no 'with' is still a contribution when the name is in
   the list, and it is the real-world defense for 'Name Live' credits.

4. Made only of recording-version keywords, so VERSION_MARKER; of cosmetic
   keywords, so COSMETIC_MARKER; of TIER_KEYWORDS, so TIER_MARKER. Precedence is
   version over cosmetic over tier.

5. Anything else is SUBTITLE: the default for a bracket or no-keyword dash-suffix
   the rules above do not claim ('Energy 52', 'a Little Bit of...').

Inside a version/cosmetic region a single Capitalized word is genuinely
ambiguous: it could be a descriptor ('Hot') or a one-word remixer ('Afrojack').
The base rules stay local: the supplied artist-name list resolves it when it
can, and when it cannot the word falls back to VERSION_MARKER / COSMETIC_MARKER
and matching just moves on, since the name is noise for the score either way.
An online lookup (MusicBrainz etc.) is not part of the base rules; it is an
optional hook for that one ambiguous case, not a dependency.

The classifier never produces an empty TITLE. If applying the rules above would
label every token as something else ('Remix', 'Acoustic', 'Intro' used as the
whole title), the whole input is reclassified as TITLE. This is the edge case
where a word that is usually a marker is in fact the song name.

Multiple contributors inside one bracket are kept together as a single
CONTRIBUTION_MARKER ('(with JENNIE, Lily Rose Depp)'); the commas joining them
are SEPARATOR inside that group, not a reason to split it.
"""


class SemanticType(StrEnum):
    CONTRIBUTION_MARKER = "contribution_marker"
    """A named person who worked on the track, not the track itself."""

    TITLE = "title"
    """The core name of the track."""

    SUBTITLE = "subtitle"
    """Bracket or trailing matter that is neither a contributor nor a marker."""

    VERSION_MARKER = "version_marker"
    """A different recording of the same work."""

    COSMETIC_MARKER = "cosmetic_marker"
    """The same recording in different paint."""

    TIER_MARKER = "tier_marker"
    """Which slot on a release this is, not which recording."""

    SEPARATOR = "separator"
    """Punctuation that delimits regions and carries no meaning of its own."""


@dataclass
class SemanticGroup:
    """A contiguous run of tokens typed as one semantic region."""

    tokens: List[GenericToken]
    """The tokens making up the region."""

    semantic_type: SemanticType
    """The semantic type assigned to the region."""

    def __str__(self) -> str:
        return ''.join(token.value for token in self.tokens)