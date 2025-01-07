import pytest

from tunesynctool.models import Track

class TestTrack:
    def test_track_str(self):
        track = Track(title='Test Track', primary_artist='Test Artist', track_number=1)
        assert str(track) == '1. - Test Artist - Test Track'

    def test_track_repr(self):
        track = Track(title='Test Track', primary_artist='Test Artist', track_number=1)
        assert repr(track) == '1. - Test Artist - Test Track'

    def test_track_equals(self):
        track1 = Track(service_id='1', service_name='spotify')
        track2 = Track(service_id='1', service_name='spotify')
        assert track1 == track2

    def test_track_dont_equal(self):
        track1 = Track(service_id='1', service_name='spotify')
        track2 = Track(service_id='2', service_name='spotify')
        assert track1 != track2

        track1 = Track(service_id='1', service_name='one')
        track2 = Track(service_id='1', service_name='another')
        assert track1 != track2

    def test_fallback_values(self):
        track = Track()
        
        assert track.title == None
        assert track.album_name == None
        assert track.primary_artist == None
        assert track.additional_artists == []
        assert track.duration_seconds == None
        assert track.track_number == None
        assert track.release_year == None
        assert track.isrc == None
        assert track.musicbrainz_id == None
        assert track.service_id == None
        assert track.service_name == 'unknown'
        assert track.service_data == {}