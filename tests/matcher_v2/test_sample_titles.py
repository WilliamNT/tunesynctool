import csv
import os

import pytest

from tunesynctool.features.v2.matcher.core import normalize_str, tokenize, group_tokens, SemanticType


def load_rows():
    path = os.path.join(os.path.dirname(__file__), 'sample_titles.csv')
    with open(path, newline='') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        return [(row[0], row[1]) for row in reader if row]


def core_of(title):
    groups = group_tokens(tokenize(normalize_str(title)), artists=None)
    parts = [str(g) for g in groups if g.semantic_type == SemanticType.TITLE]
    return ' '.join(' '.join(parts).split())


_ROWS = load_rows()


@pytest.mark.parametrize('core_title, original_title', _ROWS, ids=[t[:30] for _, t in _ROWS])
def test_core_title_matches_classifier(core_title, original_title):
    assert core_of(original_title) == core_title