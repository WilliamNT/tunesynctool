from typing import Optional, Dict
import re

# Constants for substitution patterns
ARTIST_FEATURES: Dict[str, str] = {
    'featuring': ' ', 'with': '',
    'feat.': '',     'feat': '',
    'ft.': '',       'ft': '',
    'prod. ': '',    'prod ': ''
}

CONJUNCTIONS: Dict[str, str] = {
    '&': 'and',
    '+': 'and'
}

BRACKETS: Dict[str, str] = {
    '[': '', ']': '',
    '(': '', ')': ''
}

PUNCTUATION: Dict[str, str] = {
    "'": '', '"': '',
    '!': '', '?': '',
    '/': ' ', '\\': ' ',
    '_': ' ', '-': ' ',
    '.': ' ', ',': '',
    ';': '', ':': ''
}

def __apply_substitutions(text: str, substitutions: Dict[str, str]) -> str:
    """
    Apply a dictionary of substitutions to the given text.
    """
    for old, new in substitutions.items():
        text = text.replace(old, new)
    return text

def __normalize_whitespace(text: str) -> str:
    """
    Removes extra whitespace by converting multiple spaces to single space.
    """
    return ' '.join(text.split())

def clean_str(s: Optional[str]) -> str:
    """
    Cleans a string by removing special characters and common industry terms.
    """
    if not s:
        return ''
    
    text = s.lower().strip()
    
    text = __apply_substitutions(text, ARTIST_FEATURES)
    text = __apply_substitutions(text, CONJUNCTIONS)
    text = __apply_substitutions(text, BRACKETS)
    text = __apply_substitutions(text, PUNCTUATION)
    
    return __normalize_whitespace(text)