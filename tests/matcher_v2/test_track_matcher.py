from tunesynctool.features.v2 import AsyncTrackMatcher
from tunesynctool.models import Track
from tunesynctool.drivers import AsyncWrappedServiceDriver
from bench.catalog import TargetStyle
from bench.mock_driver import MockServiceDriver


def _driver(tracks, **style):
    opts = dict(supports_direct_isrc_querying=True)
    opts.update(style)
    sync = MockServiceDriver(tracks, TargetStyle(name='mock', **opts))
    return AsyncWrappedServiceDriver(sync)


async def test_isrc_direct_returns_the_track():
    source = Track(title='Save Your Tears', primary_artist='The Weeknd', isrc='X', service_name='other')
    target = Track(title='Save Your Tears', primary_artist='The Weeknd', isrc='X', service_id='mock:1', service_name='mock')
    driver = _driver([target])
    assert await AsyncTrackMatcher(driver).find_match(source) is target


async def test_text_search_picks_canonical_over_remix_decoy():
    source = Track(title='Home (with Ariana Grande)', primary_artist='Silver Wolves', service_name='other')
    canonical = Track(title='Home', primary_artist='Silver Wolves', service_id='mock:1', service_name='mock')
    decoy = Track(title='Home (Nightcore Remix)', primary_artist='Silver Wolves', service_id='mock:1:remix', service_name='mock')
    driver = _driver([canonical, decoy])
    assert await AsyncTrackMatcher(driver).find_match(source) is canonical


async def test_absent_track_is_rejected_by_the_floor():
    source = Track(title='A Wholly Unrelated Song', primary_artist='Nobody Here', service_name='other')
    noise = Track(title='Something Else Entirely', primary_artist='Different Artist', service_id='mock:9', service_name='mock')
    driver = _driver([noise])
    assert await AsyncTrackMatcher(driver).find_match(source) is None


async def test_origin_service_fetch_matches_by_service_id():
    source = Track(title='Save Your Tears', primary_artist='The Weeknd', service_id='mock:1', service_name='mock')
    target = Track(title='Save Your Tears', primary_artist='The Weeknd', service_id='mock:1', service_name='mock')
    driver = _driver([target])
    assert await AsyncTrackMatcher(driver).find_match(source) is target


async def test_origin_service_mismatch_does_not_fetch():
    source = Track(title='Save Your Tears', primary_artist='The Weeknd', service_id='mock:1', service_name='spotify')
    target = Track(title='Save Your Tears', primary_artist='The Weeknd', service_id='mock:1', service_name='mock')
    driver = _driver([target])
    assert await AsyncTrackMatcher(driver).find_match(source) is target


async def test_isrc_not_supported_falls_through_to_text_search():
    source = Track(title='Save Your Tears', primary_artist='The Weeknd', isrc='X', service_name='other')
    target = Track(title='Save Your Tears', primary_artist='The Weeknd', isrc='X', service_id='mock:1', service_name='mock')
    driver = _driver([target], supports_direct_isrc_querying=False)
    assert await AsyncTrackMatcher(driver).find_match(source) is target


async def test_below_floor_match_is_rejected():
    source = Track(title='Save Your Tears', primary_artist='The Weeknd', service_name='other')
    weak = Track(title='Blinding Lights', primary_artist='The Weeknd', service_id='mock:1', service_name='mock')
    driver = _driver([weak])
    assert await AsyncTrackMatcher(driver).find_match(source) is None