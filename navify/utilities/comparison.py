from thefuzz import fuzz

"""
There wasn't any advanced mathematical thinking behind the following functions.
I found these ways of comparison to be the best for my use case by trial and error lol.
"""

def calculate_str_similarity(a: str, b: str) -> float:
    """
    Calculates the similarity ratio between two strings.
    Returns a float between 1 and 0.
    """

    return fuzz.ratio(a, b) / 100

def calculate_int_closeness(a: int, b: int) -> float:
    """
    Calculates the closeness between two integers.
    Returns a float between 1 and 0.
    """

    if (a == 0 or b == 0) or (a is None or b is None):
        return float(0)
    elif a == b:
        return float(1)
    
    return round(1 - abs(a - b) / max(a, b), 1)