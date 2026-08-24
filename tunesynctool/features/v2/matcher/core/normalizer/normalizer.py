import unicodedata

from .substitutions import SUBSTITUTIONS

def normalize_str(input_str: str) -> str:
    if not input_str:
        return input_str

    # Compose first: "Cafe" + combining acute becomes the single char "é", so
    # the tokenizer never sees a stray combining mark that would split a word.
    text = unicodedata.normalize("NFC", input_str)

    for old, new in SUBSTITUTIONS.items():
        text = text.replace(old, new)

    return text