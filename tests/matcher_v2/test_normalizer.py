import pytest

from tunesynctool.features.v2.matcher.core import normalize_str, tokenize, GenericTokenType


# --- the three gaps, in isolation -------------------------------------------

def test_normalize_empty_is_noop():
    assert normalize_str("") == ""


def test_normalize_plain_ascii_is_noop():
    assert normalize_str("Hello World - foo") == "Hello World - foo"


def test_en_dash_collapses_to_hyphen():
    assert normalize_str("a – b") == "a - b"


def test_em_dash_collapses_to_hyphen():
    assert normalize_str("a — b") == "a - b"


def test_decomposed_accent_is_composed():
    # "Cafe" + combining acute -> precomposed "Café" (one char fewer).
    decomposed = "Café"
    assert normalize_str(decomposed) == "Café"
    assert len(normalize_str(decomposed)) == 4


def test_already_composed_accent_is_unchanged():
    assert normalize_str("Café") == "Café"


def test_apostrophe_variants_collapse_to_ascii():
    assert normalize_str("Rock ’n’ Roll") == "Rock 'n' Roll"
    assert normalize_str("Rock ‘n‘ Roll") == "Rock 'n' Roll"
    assert normalize_str("Rock ʼnʼ Roll") == "Rock 'n' Roll"


def test_real_titles_normalize_end_to_end():
    assert normalize_str("Wonderwall – Remastered 2009") == "Wonderwall - Remastered 2009"
    assert normalize_str("L’amour toujours") == "L'amour toujours"
    assert normalize_str("Ni Tú Ni Yo") == "Ni Tú Ni Yo"


# --- end to end with the tokenizer: the gaps are gone ----------------------

def test_dash_variant_tokenizes_as_dash_after_normalize():
    toks = tokenize(normalize_str("Wonderwall – Remastered 2009"))
    assert any(t.type == GenericTokenType.DASH for t in toks)
    assert not any(t.value == "–" for t in toks)
    assert not any(t.value == "—" for t in toks)


def test_decomposed_accent_does_not_split_after_normalize():
    toks = tokenize(normalize_str("Café Del Mar"))
    alnums = [t.value for t in toks if t.type == GenericTokenType.ALPHANUMERIC]
    assert "Café" in alnums
    assert not any(t.type == GenericTokenType.UNKNOWN for t in toks)


def test_apostrophe_variant_joins_word_after_normalize():
    # After normalize, the smart-quote variant must tokenize exactly like the
    # ASCII-apostrophe one: the quotes are alphanumeric, so "'n'" is one token,
    # never an UNKNOWN smart quote lingering between words.
    smart = tokenize(normalize_str("Rock ‘n’ Roll"))
    ascii_ = tokenize("Rock 'n' Roll")
    assert smart == ascii_
    assert not any(t.type == GenericTokenType.UNKNOWN for t in smart)
    assert "'n'" in [t.value for t in smart if t.type == GenericTokenType.ALPHANUMERIC]


# --- property: normalizing twice never changes anything ---------------------

@pytest.mark.parametrize("s", [
    "",
    "Hello World",
    "Café",
    "Café",
    "a – b",
    "a — b",
    "Rock ’n’ Roll",
    "Rock ‘n‘ Roll",
    "Rock ʼnʼ Roll",
    "Wonderwall – Remastered 2009",
    "L’amour toujours",
    "Кукушка",
    "打上花火",
    "밤편지",
])
def test_normalize_is_idempotent(s):
    once = normalize_str(s)
    assert normalize_str(once) == once