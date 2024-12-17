from typing import Optional

def clean_str(s: Optional[str]) -> str:
    """Cleans a string by removing special characters and common industry words and whitespace."""
    
    if not s:
        return ''
    
    substitutions = {
        # Artist features
        'feat.': '',     'feat': '',
        'ft.': '',       'ft': '',
        'featuring': '', 'with': '',
        'prod.': '',     'prod': '',
        
        # Conjunctions
        '&': 'and',
        '+': 'and',
        
        # Brackets and parentheses
        '[': '', ']': '',
        '(': '', ')': '',
        
        # Quotation marks and punctuation
        "'": '', '"': '',
        '!': '', '?': '',
        
        # Separators
        '/': ' ',  '\\': ' ',
        '_': ' ',  '-': ' ',
        '.': '',   ',': '',
        ';': '',   ':': ''
    }
    
    normalized = s.lower().strip()
    for old, new in substitutions.items():
        normalized = normalized.replace(old, new)
    
    return ' '.join(normalized.split())

