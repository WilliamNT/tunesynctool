from typing import Optional, Dict
import re

# Constants for substitution patterns
ARTIST_FEATURES: Dict[str, str] = {
    'featuring': ' ',
    'with': '',
    'feat.': '',
    'feat': '',
    'ft.': '',
    'ft': '',
    'prod. ': '',
    'prod ': '',
    'w/': '',
}

CONJUNCTIONS: Dict[str, str] = {
    '&': 'and',
    '+': 'and',
}

BRACKETS: Dict[str, str] = {
    '[': '',
    ']': '',
    '(': '',
    ')': '',
}

PUNCTUATION: Dict[str, str] = {
    "'": '',
    '"': '',
    '!': '',
    '?': '',
    '/': ' ',
    '\\': ' ',
    '_': ' ',
    '-': ' ',
    '.': ' ',
    ',': '',
    ';': '',
    ':': '',
}

def __apply_substitutions(text: str, substitutions: Dict[str, str]) -> str:
    """
    Apply a dictionary of substitutions to the given text.

    :param text: The text to apply substitutions to.
    :param substitutions: A dictionary of substitutions to apply.
    :return: The text with substitutions applied.
    """

    for old, new in substitutions.items():
        text = text.replace(old, new)

    return text

def __normalize_whitespace(text: str) -> str:
    """
    Removes extra whitespace by converting multiple spaces to single space.

    :param text: The text to clean.
    :return: The cleaned text.
    """

    return ' '.join(text.split())

def __remove_version_tags(text: str) -> str:
    """
    Removes version-related tags like (album version), (remix), (live), etc.
    Ensures that removed content does not leave unnecessary double spaces.

    :param text: The text to clean.
    :return: The cleaned text.
    """

    return re.sub(r'\s*[\(\{\[][^()\[\]{}]*[\)\}\]]\s*', ' ', text)


def clean_str(s: Optional[str]) -> str:
    """
    Cleans a string by removing special characters, common industry terms, and version tags.

    :param s: The string to clean.
    :return: The cleaned string or an empty string if the input is None.
    """

    if not s:
        return ''
    
    text = s.lower().strip()
    
    text = __remove_version_tags(text)
    text = __apply_substitutions(text, ARTIST_FEATURES)
    text = __apply_substitutions(text, CONJUNCTIONS)
    text = __apply_substitutions(text, BRACKETS)
    text = __apply_substitutions(text, PUNCTUATION)
    
    return __normalize_whitespace(text)
