from tunesynctool.features.v2 import match_track
from tunesynctool.models import Track


def track(title=None, **kw):
    return Track(title=title, **kw)


def test_match_picks_highest_score():
    source = track('Save Your Tears', primary_artist='The Weeknd')
    good = track('Save Your Tears', primary_artist='The Weeknd')
    bad = track('Blinding Lights', primary_artist='The Weeknd')
    assert match_track(source, [bad, good]) is good


def test_match_threshold_filters():
    source = track('Save Your Tears', primary_artist='The Weeknd')
    bad = track('Blinding Lights', primary_artist='The Weeknd')
    assert match_track(source, [bad], threshold=0.9) is None


def test_match_keeps_above_threshold_when_below_skipped():
    source = track('Save Your Tears', primary_artist='The Weeknd')
    good = track('Save Your Tears', primary_artist='The Weeknd')
    bad = track('Blinding Lights', primary_artist='The Weeknd')
    assert match_track(source, [bad, good], threshold=0.9) is good


def test_match_empty_candidates_returns_none():
    source = track('Save Your Tears', primary_artist='The Weeknd')
    assert match_track(source, []) is None
    assert match_track(source, None) is None


def test_match_skips_none_candidates():
    source = track('Save Your Tears', primary_artist='The Weeknd')
    good = track('Save Your Tears', primary_artist='The Weeknd')
    assert match_track(source, [None, good]) is good


def test_match_tiebreak_prefers_tighter_duration():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=200)
    a = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205)
    b = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=209)
    assert match_track(source, [b, a]) is a


def test_match_tiebreak_is_deterministic_by_service_id():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205)
    a = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205, service_id='aaa')
    b = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205, service_id='bbb')
    assert match_track(source, [a, b]) is a
    assert match_track(source, [b, a]) is a


def test_match_tiebreak_prefers_more_complete():
    source = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205)
    fuller = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205, album_name='After Hours', service_id='z')
    sparser = track('Save Your Tears', primary_artist='The Weeknd', duration_seconds=205, service_id='y')
    assert match_track(source, [sparser, fuller]) is fuller