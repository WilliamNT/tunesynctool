import pytest

from tunesynctool.features.v2.matcher.core import GenericToken, GenericTokenType, tokenize
from tunesynctool.features.v2.matcher.core.tokenizer.tokenizer import _identify_token_type


# --- helpers -----------------------------------------------------------------

def tok(value: str, type_: GenericTokenType) -> GenericToken:
    return GenericToken(value=value, type=type_)


def values(tokens):
    return [t.value for t in tokens]


def types(tokens):
    return [t.type for t in tokens]


# --- basic cases --------------------------------------------------------------

def test_empty_string_produces_no_tokens():
    assert tokenize("") == []


def test_single_word_is_one_alphanumeric_token():
    assert tokenize("Hello") == [tok("Hello", GenericTokenType.ALPHANUMERIC)]


def test_whitespace_separates_words():
    assert tokenize("Hello World") == [
        tok("Hello", GenericTokenType.ALPHANUMERIC),
        tok(" ", GenericTokenType.SPACE),
        tok("World", GenericTokenType.ALPHANUMERIC),
    ]


def test_consecutive_spaces_are_grouped_into_one_token():
    assert tokenize("Hello   World") == [
        tok("Hello", GenericTokenType.ALPHANUMERIC),
        tok("   ", GenericTokenType.SPACE),
        tok("World", GenericTokenType.ALPHANUMERIC),
    ]


def test_leading_and_trailing_whitespace_are_preserved():
    assert tokenize("  hi  ") == [
        tok("  ", GenericTokenType.SPACE),
        tok("hi", GenericTokenType.ALPHANUMERIC),
        tok("  ", GenericTokenType.SPACE),
    ]


def test_tabs_and_newlines_are_whitespace():
    # Every isspace() character maps to SPACE and consecutive ones group.
    assert tokenize("a\t b\nc") == [
        tok("a", GenericTokenType.ALPHANUMERIC),
        tok("\t ", GenericTokenType.SPACE),
        tok("b", GenericTokenType.ALPHANUMERIC),
        tok("\n", GenericTokenType.SPACE),
        tok("c", GenericTokenType.ALPHANUMERIC),
    ]


# --- alphanumeric grouping ----------------------------------------------------

def test_digits_are_alphanumeric():
    assert tokenize("123") == [tok("123", GenericTokenType.ALPHANUMERIC)]


def test_letters_and_digits_group_together():
    assert tokenize("abc123") == [tok("abc123", GenericTokenType.ALPHANUMERIC)]


@pytest.mark.parametrize("apostrophe", ["'", "’"])
def test_apostrophes_are_treated_as_alphanumeric(apostrophe):
    assert tokenize(f"It{apostrophe}s") == [
        tok(f"It{apostrophe}s", GenericTokenType.ALPHANUMERIC)
    ]


def test_apostrophe_does_not_split_word():
    assert tokenize("don't stop") == [
        tok("don't", GenericTokenType.ALPHANUMERIC),
        tok(" ", GenericTokenType.SPACE),
        tok("stop", GenericTokenType.ALPHANUMERIC),
    ]


# --- reserved symbols ---------------------------------------------------------

@pytest.mark.parametrize("char,token_type", [
    ("(", GenericTokenType.LPAREN),
    (")", GenericTokenType.RPAREN),
    (",", GenericTokenType.COMMA),
    ("-", GenericTokenType.DASH),
    ("/", GenericTokenType.SLASH),
    ("&", GenericTokenType.AMPERSAND),
    ("+", GenericTokenType.PLUS),
    (";", GenericTokenType.SEMICOLON),
])
def test_each_reserved_symbol_maps_to_its_type(char, token_type):
    assert tokenize(char) == [tok(char, token_type)]


def test_different_reserved_symbols_become_separate_tokens():
    assert tokenize("()") == [
        tok("(", GenericTokenType.LPAREN),
        tok(")", GenericTokenType.RPAREN),
    ]


def test_consecutive_identical_reserved_symbols_group():
    assert tokenize("--") == [tok("--", GenericTokenType.DASH)]
    assert tokenize("//") == [tok("//", GenericTokenType.SLASH)]
    assert tokenize("&&&") == [tok("&&&", GenericTokenType.AMPERSAND)]


def test_reserved_symbol_between_words_is_its_own_token():
    assert tokenize("Rock & Roll") == [
        tok("Rock", GenericTokenType.ALPHANUMERIC),
        tok(" ", GenericTokenType.SPACE),
        tok("&", GenericTokenType.AMPERSAND),
        tok(" ", GenericTokenType.SPACE),
        tok("Roll", GenericTokenType.ALPHANUMERIC),
    ]


def test_parentheses_wrap_a_word():
    assert tokenize("(remix)") == [
        tok("(", GenericTokenType.LPAREN),
        tok("remix", GenericTokenType.ALPHANUMERIC),
        tok(")", GenericTokenType.RPAREN),
    ]


def test_dash_and_slash_are_separators_not_alphanumeric():
    assert tokenize("a-b/c") == [
        tok("a", GenericTokenType.ALPHANUMERIC),
        tok("-", GenericTokenType.DASH),
        tok("b", GenericTokenType.ALPHANUMERIC),
        tok("/", GenericTokenType.SLASH),
        tok("c", GenericTokenType.ALPHANUMERIC),
    ]


# --- unknown characters -------------------------------------------------------

def test_unknown_character_is_its_own_token_type():
    assert tokenize("!") == [tok("!", GenericTokenType.UNKNOWN)]


def test_consecutive_unknown_characters_group():
    assert tokenize("!!!") == [tok("!!!", GenericTokenType.UNKNOWN)]


def test_unknown_character_separates_alphanumeric_runs():
    assert tokenize("a!b") == [
        tok("a", GenericTokenType.ALPHANUMERIC),
        tok("!", GenericTokenType.UNKNOWN),
        tok("b", GenericTokenType.ALPHANUMERIC),
    ]


# --- realistic / complex strings ---------------------------------------------

def test_complex_tracklike_string():
    assert tokenize("Hello (World) - Pt. 2") == [
        tok("Hello", GenericTokenType.ALPHANUMERIC),
        tok(" ", GenericTokenType.SPACE),
        tok("(", GenericTokenType.LPAREN),
        tok("World", GenericTokenType.ALPHANUMERIC),
        tok(")", GenericTokenType.RPAREN),
        tok(" ", GenericTokenType.SPACE),
        tok("-", GenericTokenType.DASH),
        tok(" ", GenericTokenType.SPACE),
        tok("Pt", GenericTokenType.ALPHANUMERIC),
        tok(".", GenericTokenType.UNKNOWN),
        tok(" ", GenericTokenType.SPACE),
        tok("2", GenericTokenType.ALPHANUMERIC),
    ]


def test_repeated_calls_are_independent():
    first = tokenize("ab cd")
    second = tokenize("xy z")
    assert values(first) == ["ab", " ", "cd"]
    assert values(second) == ["xy", " ", "z"]


# --- property-style invariants ------------------------------------------------
# These encode general rules a correct tokenizer must satisfy, regardless of
# the specific input. They are the most effective at exposing the current
# implementation's bugs.

# Real catalog titles, kept broad on purpose: accented Latin, Cyrillic, CJK,
# Korean, featuring clauses, bracket nesting, dash separators, periods in
# abbreviations. The property tests below run over all of them, so the
# tokenizer is held to its invariants on the shapes that actually show up in
# music metadata, not just hand-picked ASCII.
REAL_WORLD_TITLES = [
    "God's Plan",
    "Don't Start Now",
    "Where'd You Go",
    "L'amour toujours",
    "L’amour toujours",
    "Ni Tú Ni Yo",
    "Bésame Mucho",
    "Señorita",
    "Für Elise",
    "Aïcha",
    "Ça fait mal",
    "Sigur Rós",
    "Mötley Crüe",
    "Los Ángeles Azules",
    "Кукушка",
    "Группа крови",
    "打上花火",
    "前前前世",
    "밤편지",
    "봄날",
    "Boy With Luv (feat. Halsey)",
    "Sour Candy (with BLACKPINK)",
    "Rain On Me (with Ariana Grande)",
    "Lucid Dreams (Remix) [feat. Lil Wayne]",
    "Wonderwall - Remastered 2009",
    "Symphony No. 5 in C minor, Op. 67",
    "XO TOUR Llif3",
    "SAD!",
    "the 1",
    "Café Del Mar",
]

@pytest.mark.parametrize("s", [
    "",
    "Hello",
    "Hello World",
    "Hello   World",
    "  hi  ",
    "Rock & Roll",
    "(remix)",
    "a-b/c",
    "don't stop",
    "Hello (World) - Pt. 2",
    "!!@#",
    "a , b ; c + d",
    "\t\n x ",
] + REAL_WORLD_TITLES)
def test_round_trip_concatenation_of_token_values_equals_input(s):
    # No character may be dropped or duplicated.
    assert "".join(values(tokenize(s))) == s


@pytest.mark.parametrize("s", [
    "Hello World",
    "Hello   World",
    "Rock & Roll",
    "(remix)",
    "a-b/c",
    "don't stop",
    "Hello (World) - Pt. 2",
    "!!@#",
    "a , b ; c + d",
    "\t\n x ",
] + REAL_WORLD_TITLES)
def test_every_token_has_a_consistent_type(s):
    # Every character within a token must classify as the same type that
    # the token carries, and consecutive tokens must differ in type.
    tokens = tokenize(s)
    for token in tokens:
        assert token.value, f"empty token in {s!r}: {tokens}"
        expected = _identify_token_type(token.value[0])
        assert token.type == expected, (
            f"token {token!r} labelled {token.type} but its first char "
            f"classifies as {expected} (input {s!r})"
        )
        for ch in token.value:
            assert _identify_token_type(ch) == token.type, (
                f"token {token!r} contains char {ch!r} that classifies "
                f"differently from {token.type} (input {s!r})"
            )
    for a, b in zip(tokens, tokens[1:]):
        assert a.type != b.type, (
            f"two consecutive tokens share type {a.type} and should have "
            f"been merged: {a!r} {b!r} (input {s!r})"
        )


def test_identify_token_type_space_variants():
    for ch in [" ", "\t", "\n", "\r"]:
        assert _identify_token_type(ch) == GenericTokenType.SPACE


def test_identify_token_type_apostrophes_are_alphanumeric():
    assert _identify_token_type("'") == GenericTokenType.ALPHANUMERIC
    assert _identify_token_type("’") == GenericTokenType.ALPHANUMERIC


def test_identify_token_type_reserved_symbols():
    for char, token_type in [
        ("(", GenericTokenType.LPAREN),
        (")", GenericTokenType.RPAREN),
        ("[", GenericTokenType.LPAREN),
        ("]", GenericTokenType.RPAREN),
        ("{", GenericTokenType.LPAREN),
        ("}", GenericTokenType.RPAREN),
        (",", GenericTokenType.COMMA),
        ("-", GenericTokenType.DASH),
        ("/", GenericTokenType.SLASH),
        ("&", GenericTokenType.AMPERSAND),
        ("+", GenericTokenType.PLUS),
        (";", GenericTokenType.SEMICOLON),
    ]:
        assert _identify_token_type(char) == token_type


def test_identify_token_type_unknown_falls_through():
    for ch in ["!", "@", "#", "%", ".", "_"]:
        assert _identify_token_type(ch) == GenericTokenType.UNKNOWN


# --- realistic title cases ----------------------------------------------------
# The 11 track-title inputs used to validate the (fixed) tokenizer end to end.
# Each case asserts the full expected token list, so any regression in
# grouping, type labeling, or character preservation surfaces directly.

T = GenericTokenType  # short alias to keep the expected lists readable

TITLE_CASES = [
    (
        "Overdrive (feat. Norma Jean Martine) (Cloned Version)",
        [
            tok("Overdrive", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("feat", T.ALPHANUMERIC), tok(".", T.UNKNOWN),
            tok(" ", T.SPACE), tok("Norma", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Jean", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Martine", T.ALPHANUMERIC), tok(")", T.RPAREN), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("Cloned", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Version", T.ALPHANUMERIC), tok(")", T.RPAREN),
        ],
    ),
    (
        "Újra úton - Sterbinszky x Mynea Remix",
        [
            tok("Újra", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("úton", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("Sterbinszky", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("x", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Mynea", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remix", T.ALPHANUMERIC),
        ],
    ),
    (
        "raindrops (an angel cried)",
        [
            tok("raindrops", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("an", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("angel", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("cried", T.ALPHANUMERIC), tok(")", T.RPAREN),
        ],
    ),
    (
        "It Ain't Me (with Selena Gomez)",
        [
            tok("It", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Ain't", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Me", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("with", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Selena", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Gomez", T.ALPHANUMERIC), tok(")", T.RPAREN),
        ],
    ),
    (
        "UFO (feat. Solamay)",
        [
            tok("UFO", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("feat", T.ALPHANUMERIC), tok(".", T.UNKNOWN),
            tok(" ", T.SPACE), tok("Solamay", T.ALPHANUMERIC), tok(")", T.RPAREN),
        ],
    ),
    (
        "Sweet Dreams (Are Made of This) - Hot Remix / 2005 Remaster",
        [
            tok("Sweet", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Dreams", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("Are", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Made", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("of", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("This", T.ALPHANUMERIC), tok(")", T.RPAREN), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("Hot", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remix", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("/", T.SLASH), tok(" ", T.SPACE),
            tok("2005", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remaster", T.ALPHANUMERIC),
        ],
    ),
    (
        "Satellites - MaRLo Radio Edit",
        [
            tok("Satellites", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("MaRLo", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Radio", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Edit", T.ALPHANUMERIC),
        ],
    ),
    (
        "Don't Be so Shy - Filatov & Karas Remix",
        [
            tok("Don't", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Be", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("so", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Shy", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("Filatov", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("&", T.AMPERSAND), tok(" ", T.SPACE),
            tok("Karas", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remix", T.ALPHANUMERIC),
        ],
    ),
    (
        "Work from Home (feat. Ty Dolla $ign)",
        [
            tok("Work", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("from", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Home", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("feat", T.ALPHANUMERIC), tok(".", T.UNKNOWN),
            tok(" ", T.SPACE), tok("Ty", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Dolla", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("$", T.UNKNOWN), tok("ign", T.ALPHANUMERIC), tok(")", T.RPAREN),
        ],
    ),
    (
        "Pretty Girl - Cheat Codes X CADE Remix",
        [
            tok("Pretty", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Girl", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("Cheat", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Codes", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("X", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("CADE", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remix", T.ALPHANUMERIC),
        ],
    ),
    (
        "The Made Up Band - Jump, Run, Go (ft. Somebody Else) (CoolDJ REMIX) [2023 Remaster]",
        [
            tok("The", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Made", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Up", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Band", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("-", T.DASH), tok(" ", T.SPACE),
            tok("Jump", T.ALPHANUMERIC), tok(",", T.COMMA), tok(" ", T.SPACE),
            tok("Run", T.ALPHANUMERIC), tok(",", T.COMMA), tok(" ", T.SPACE),
            tok("Go", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("ft", T.ALPHANUMERIC), tok(".", T.UNKNOWN),
            tok(" ", T.SPACE), tok("Somebody", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Else", T.ALPHANUMERIC), tok(")", T.RPAREN), tok(" ", T.SPACE),
            tok("(", T.LPAREN), tok("CoolDJ", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("REMIX", T.ALPHANUMERIC), tok(")", T.RPAREN), tok(" ", T.SPACE),
            tok("[", T.LPAREN), tok("2023", T.ALPHANUMERIC), tok(" ", T.SPACE),
            tok("Remaster", T.ALPHANUMERIC), tok("]", T.RPAREN),
        ],
    ),
]


@pytest.mark.parametrize(
    "title,expected",
    TITLE_CASES,
    ids=[c[0][:32] for c in TITLE_CASES],
)
def test_title_tokenization(title, expected):
    assert tokenize(title) == expected


@pytest.mark.parametrize("title,_expected", TITLE_CASES, ids=[c[0][:32] for c in TITLE_CASES])
def test_title_round_trip(title, _expected):
    assert "".join(values(tokenize(title))) == title


@pytest.mark.parametrize("title,_expected", TITLE_CASES, ids=[c[0][:32] for c in TITLE_CASES])
def test_title_no_adjacent_same_type(title, _expected):
    tokens = tokenize(title)
    for a, b in zip(tokens, tokens[1:]):
        assert a.type != b.type, f"adjacent tokens share type {a.type}: {a!r} {b!r}"