import sys
from pathlib import Path
from copy import deepcopy
import hashlib
from random import Random as RNG
from typing import List, Optional
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tunesynctool.models import Track

"""
These utilities help us mutate tracks in a reproducable way.

We use a deterministic seed for our random number generator, meaning every person
running the benchmark should get the same benchmark result for the **same code and dataset version**.
"""

FEATURE_KEYWORDS = {
    "featuring", "feat", "feat.",
    "ft.", "prod.", "prod. by", "prod by",
    "by", "w.", "w/", "with",
}

BOUNDARIES = {
    ("(", ")"),
    ("[", "]"),
    ("{", "}"),
    ("/", "/"),
    ("- ", ""),
    ("– ", ""),
    ("— ", ""),
}

COMMANS = {",", ";",}

VERSION_KEYWORDS = {
    "Remix", "Cover", "Edit", "Radio Edit", "VIP", "V.I.P.", "VIP.",
    "Club", "Slowed down", "Reverb", "Slowed down + reverb", "slowed+reverb",
    "slowed", "epic", "orchestra", "orchestral"
}

# Reissue tags. A remastered/live/acoustic track is still the same recording,
# so a good scorer must not punish these the way it punishes a stray "Remix".
RERELEASE_KEYWORDS = {
    "Remastered", "Remastered Version", "Remastered 2009",
    "Live", "Live Version", "Live at Wembley",
    "Acoustic", "Acoustic Version",
    "Instrumental", "Instrumental Version",
    "Mono Version", "Stereo Version",
    "Demo",
}

# Pure YouTube noise. A matcher should ignore these entirely.
OFFICIAL_SUFFIXES = {
    "Official Audio", "Official Video", "Official Music Video",
    "Lyric Video", "Visualizer", "Audio", "HD Audio",
}

DASH_VARIANTS = {"-", "–", "—", "−"}
APOSTROPHE_VARIANTS = {"'", "'", "ʼ"}
VOWELS = set("aeiouAEIOU")

VARIOUS_ARTISTS_NAMES = {"Various Artists", "VA", "Various", "Unknown Artist"}

ALBUM_SUFFIXES = {
    " (Deluxe Edition)",
    " (Remastered)",
    " (20th Anniversary)",
    " (Expanded Edition)",
    " (Original Motion Picture Soundtrack)",
}

TRACK_NUMBER_SEPARATORS = {" - ", ". ", "_", " "}

def get_deterministic_rng(track_identifier: str, iteration: int) -> RNG:
    """
    Generates an isolated, deterministic RNG based on track ID and iteration.

    :param track_identifier: Anything that is unique to the track.
    :param iteration: Self explanatory.
    :return: A unique, seeded random number generator.
    """

    unique_str = f"{track_identifier}_{iteration}"

    seed_bytes = hashlib.md5(unique_str.encode("utf-8")).digest()
    seed_int = int.from_bytes(seed_bytes, byteorder="big")

    return RNG(seed_int)


def add_tokens(values: List[str], after_boundary: Optional[str], rng: RNG) -> Optional[str]:
    chunk = ""

    use_boundaries = rng.choice([True, False])
    boundaries = rng.choice(sorted(BOUNDARIES))

    if use_boundaries:
        chunk += boundaries[0]

    if after_boundary:
        chunk += rng.choice([after_boundary.lower(), after_boundary.upper()])

    if values:
        if after_boundary:
            chunk += " "
        join_all = len(values) > 1 and rng.choice([True, False])
        if join_all:
            chunk += f"{rng.choice(sorted(COMMANS))} ".join(values)
        else:
            chunk += rng.choice(sorted(values))

    if use_boundaries:
        chunk += boundaries[1]

    return chunk

def generate_features(base_track: Track, rng: RNG) -> Optional[str]:
    # Can and should we add features?
    if len(base_track.additional_artists) == 0 or not rng.choice([True, False]):
        return None

    pattern = re.compile(
        r"\b(?:featuring|feat\.?|ft\.|prod\.?(?: by)?|by|w\.|w/|with)\b",
        re.IGNORECASE,
    )

    # Title already contains features
    if base_track.title and pattern.search(base_track.title):
        return None

    return add_tokens(
        values=base_track.additional_artists,
        after_boundary=rng.choice(sorted(FEATURE_KEYWORDS)),
        rng=rng
    )

def generate_edition(base_track: Track, rng: RNG) -> Optional[str]:
    pattern = re.compile(
        r"\b(?:"
        r"radio edit|"
        r"slowed down \+ reverb|"
        r"slowed\+reverb|"
        r"v\.i\.p\.|"
        r"vip\.?|"
        r"remix|"
        r"cover|"
        r"edit|"
        r"club|"
        r"slowed down|"
        r"reverb|"
        r"slowed|"
        r"epic|"
        r"orchestral|"
        r"orchestra"
        r")\b",
        re.IGNORECASE,
    )

    # Title already contains version keyword
    if base_track.title and pattern.search(base_track.title):
        return None

    is_remix = rng.choice([True, False])
    if is_remix:
        # A named remixer turns a bare "Remix" into "X Remix" when we have one to credit.
        if base_track.additional_artists and rng.choice([True, False]):
            remixer = rng.choice(sorted(base_track.additional_artists))
            keyword = f"{remixer} Remix"
        else:
            keyword = "Remix"
    else:
        keyword = rng.choice(sorted([k for k in VERSION_KEYWORDS if k.lower() != "remix"]))

    opener, closer = rng.choice(sorted(BOUNDARIES))
    chunk = f"{opener}{keyword}{closer}"

    return chunk

def generate_rerelease_marker(base_track: Track, rng: RNG) -> Optional[str]:
    pattern = re.compile(
        r"\b(?:remastered|live|acoustic|instrumental|mono|stereo|demo)\b",
        re.IGNORECASE,
    )

    if base_track.title and pattern.search(base_track.title):
        return None

    keyword = rng.choice(sorted(RERELEASE_KEYWORDS))
    opener, closer = rng.choice(sorted(BOUNDARIES))

    return f"{opener}{keyword}{closer}"

def generate_official_suffix(base_track: Track, rng: RNG) -> Optional[str]:
    keyword = rng.choice(sorted(OFFICIAL_SUFFIXES))
    opener, closer = rng.choice(sorted(BOUNDARIES))

    return f"{opener}{keyword}{closer}"

def generate_track_number_prefix(rng: RNG) -> str:
    number = rng.randint(1, 20)
    sep = rng.choice(sorted(TRACK_NUMBER_SEPARATORS))

    return f"{number:02d}{sep}"

def corrupt_case(text: str, rng: RNG) -> str:
    mode = rng.choice(sorted({"upper", "lower", "title", "swapcase"}))

    if mode == "upper":
        return text.upper()
    if mode == "lower":
        return text.lower()
    if mode == "title":
        return text.title()

    return text.swapcase()

def corrupt_punctuation(text: str, rng: RNG) -> str:
    if "-" in text:
        text = text.replace("-", rng.choice(sorted(DASH_VARIANTS)))
    if "'" in text:
        text = text.replace("'", rng.choice(sorted(APOSTROPHE_VARIANTS)))
    if rng.choice([True, False]):
        text = f" {text} "

    return text

def inject_typo(text: str, rng: RNG) -> str:
    if not text or len(text) < 3:
        return text

    kind = rng.choice(sorted({"transpose", "double", "drop", "vowel"}))
    chars = list(text)

    if kind == "transpose":
        idx = rng.randint(0, len(chars) - 2)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    elif kind == "double":
        idx = rng.randint(0, len(chars) - 1)
        chars.insert(idx, chars[idx])
    elif kind == "drop":
        idx = rng.randint(0, len(chars) - 1)
        del chars[idx]
    else:
        vowel_positions = [i for i, c in enumerate(chars) if c in VOWELS]
        if not vowel_positions:
            return text
        idx = rng.choice(vowel_positions)
        chars[idx] = rng.choice(sorted(VOWELS - {chars[idx]}))

    return "".join(chars)

def mutate_title(track: Track, rng: RNG) -> str:
    title = track.title or ""

    # Filename-style "Artist - Title", artist kept as-is.
    if rng.random() < 0.20 and track.primary_artist:
        title = f"{track.primary_artist} - {title}"

    # Leading track number from a ripped filename.
    if rng.random() < 0.25:
        title = f"{generate_track_number_prefix(rng)}{title}"

    chunk = generate_features(track, rng)
    if chunk:
        title = f"{title} {chunk}"

    if rng.random() < 0.40:
        chunk = generate_edition(track, rng)
        if chunk:
            title = f"{title} {chunk}"

    if rng.random() < 0.15:
        chunk = generate_rerelease_marker(track, rng)
        if chunk:
            title = f"{title} {chunk}"

    if rng.random() < 0.10:
        chunk = generate_official_suffix(track, rng)
        if chunk:
            title = f"{title} {chunk}"

    if rng.random() < 0.20:
        title = corrupt_case(title, rng)
    if rng.random() < 0.20:
        title = corrupt_punctuation(title, rng)
    if rng.random() < 0.15:
        title = inject_typo(title, rng)

    return title.strip()

def mutate_artist(track: Track, rng: RNG) -> None:
    if not track.primary_artist:
        return

    # Compilation mis-tag: the real artist is only recoverable elsewhere.
    if rng.random() < 0.10:
        track.primary_artist = rng.choice(sorted(VARIOUS_ARTISTS_NAMES))
        track.additional_artists = []
        return

    # "The Weeknd" <-> "Weeknd, The"
    if rng.random() < 0.15:
        if track.primary_artist.startswith("The "):
            track.primary_artist = f"{track.primary_artist[4:]}, The"
        else:
            track.primary_artist = f"The {track.primary_artist}"

    # Featured artists collapsed into the primary as one joined string.
    if track.additional_artists and rng.random() < 0.25:
        joiner = rng.choice(sorted({" & ", " x ", ", ", " + "}))
        track.primary_artist = track.primary_artist + joiner + joiner.join(track.additional_artists)
        track.additional_artists = []

    # Trailing word dropped ("The Weeknd" -> "The").
    if rng.random() < 0.10:
        parts = track.primary_artist.split()
        if len(parts) > 1:
            track.primary_artist = " ".join(parts[:-1])

    if rng.random() < 0.15:
        track.primary_artist = corrupt_case(track.primary_artist, rng)

    # Transposition typo in the artist name.
    if rng.random() < 0.10 and len(track.primary_artist) > 3:
        artist_chars = list(track.primary_artist)
        idx = rng.randint(0, len(artist_chars) - 2)
        artist_chars[idx], artist_chars[idx + 1] = artist_chars[idx + 1], artist_chars[idx]
        track.primary_artist = "".join(artist_chars)

def apply_structural_mutations(track: Track, rng: RNG) -> None:
    roll = rng.random()

    if roll < 0.10:
        # Artist and title swapped.
        track.title, track.primary_artist = track.primary_artist, track.title
    elif roll < 0.20:
        # Featured artists folded into the title as a feat clause.
        if track.additional_artists and track.title:
            keyword = rng.choice(sorted(FEATURE_KEYWORDS))
            names = " ".join(track.additional_artists)
            track.title = f"{track.title} {keyword} {names}"
            track.additional_artists = []
    elif roll < 0.25:
        # Everything jammed into the title; artist and album stripped.
        if track.title and track.primary_artist:
            track.title = f"{track.primary_artist} - {track.title}"
        track.primary_artist = None
        track.album_name = None
        track.additional_artists = []

def generate_candidate_track(base_track: Track, rng: RNG) -> Track:
    """
    Deterministically mutates a track using the provided RNG.
    """

    base_track.service_data = None
    
    mutated = deepcopy(base_track)

    # We strip these so the algorithms can't short circuit based on them.
    mutated.musicbrainz_id = None
    mutated.isrc = None

    apply_structural_mutations(mutated, rng)

    if mutated.title:
        mutated.title = mutate_title(mutated, rng)

    mutate_artist(mutated, rng)

    if rng.random() < 0.30:
        mutated.album_name = None
    elif rng.random() < 0.10:
        mutated.album_name = mutated.title
    elif rng.random() < 0.10 and mutated.album_name:
        mutated.album_name = f"{mutated.album_name}{rng.choice(sorted(ALBUM_SUFFIXES))}"

    if rng.random() < 0.30:
        mutated.release_year = None

    if rng.random() < 0.30:
        mutated.track_number = None

    if mutated.duration_seconds:
        roll = rng.random()
        if roll < 0.15:
            mutated.duration_seconds = None
        elif roll < 0.25:
            mutated.duration_seconds = (mutated.duration_seconds // 60) * 60
        elif roll < 0.35:
            mutated.duration_seconds = mutated.duration_seconds + rng.choice([-3, -2, 2, 3, 5])
        else:
            mutated.duration_seconds = max(1, mutated.duration_seconds + int(rng.gauss(0, 3)))

    return mutated