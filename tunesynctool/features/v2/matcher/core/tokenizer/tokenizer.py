from typing import List, Optional

from .generic_token import GenericTokenType, GenericToken

_RESERVED_SYMBOLS = {
    "{": GenericTokenType.LPAREN,
    "}": GenericTokenType.RPAREN,
    "[": GenericTokenType.LPAREN,
    "]": GenericTokenType.RPAREN,
    "(": GenericTokenType.LPAREN,
    ")": GenericTokenType.RPAREN,
    ",": GenericTokenType.COMMA,
    "-": GenericTokenType.DASH,
    "/": GenericTokenType.SLASH,
    "&": GenericTokenType.AMPERSAND,
    "+": GenericTokenType.PLUS,
    ";": GenericTokenType.SEMICOLON,
}

def _identify_token_type(character: str) -> GenericTokenType:
    if character.isspace():
        return GenericTokenType.SPACE

    if character.isalnum() or character in {"'", "’"}:
        return GenericTokenType.ALPHANUMERIC

    if character in _RESERVED_SYMBOLS:
        return _RESERVED_SYMBOLS[character]

    return GenericTokenType.UNKNOWN

def tokenize(input_str: str) -> List[GenericToken]:
    tokens: List[GenericToken] = []
    buffer: List[str] = []
    suspected_token_type: Optional[GenericTokenType] = None
    index = 0

    def _has_next() -> bool:
        return index + 1 < len(input_str)

    def _peek(offset: int) -> str:
        return input_str[index + offset]

    def _save_buffer() -> None:
        nonlocal suspected_token_type
        
        if not buffer:
            return

        token = GenericToken(
            value="".join(buffer),
            type=suspected_token_type,
        )

        tokens.append(token)
        buffer.clear()
        suspected_token_type = None

    def _bufferize_or_save(character: str) -> None:
        nonlocal suspected_token_type

        if suspected_token_type is None:
            suspected_token_type = _identify_token_type(character)

        buffer.append(character)

        if not _has_next():
            _save_buffer()
            return

        next_character = _peek(1)
        type_of_next_character = _identify_token_type(next_character)

        if suspected_token_type != type_of_next_character:
            _save_buffer()

    while index < len(input_str):
        character: str = input_str[index]
        _bufferize_or_save(character)
        index += 1

    return tokens