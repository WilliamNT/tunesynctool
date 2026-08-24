from enum import StrEnum
from dataclasses import dataclass

class GenericTokenType(StrEnum):
    LPAREN = "l_paren"
    RPAREN = "r_paren"

    ALPHANUMERIC = "alphanumeric"
    SPACE = "space"

    DASH = "dash"
    SLASH = "slash"
    AMPERSAND = "ampersand"
    COMMA = "comma"
    PLUS = "plus"
    SEMICOLON = "semicolon"

    SYMBOL = "symbol"
    UNKNOWN = "unknown"

@dataclass
class GenericToken:
    value: str
    type: GenericTokenType
    