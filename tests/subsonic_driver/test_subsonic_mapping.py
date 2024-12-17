import json
import pytest

MOCK_SUBSONIC_TRACK_RESPONSE = None
with open('tests/mock/subsonic_track.json', 'r') as f:
    MOCK_SUBSONIC_TRACK_RESPONSE = json.load(f)

MOCK_SUBSONIC_PLAYLIST_RESPONSE = None
with open('tests/mock/subsonic_playlist.json', 'r') as f:
    MOCK_SUBSONIC_PLAYLIST_RESPONSE = json.load(f)

from navify.drivers.common.subsonic import SubsonicMapper

@pytest.fixture
def subsonic_mapper():
    return SubsonicMapper()

class TestPlaylistMapping:
    def test_map_playlist(self, subsonic_mapper: SubsonicMapper):
        playlist = subsonic_mapper.map_playlist(MOCK_SUBSONIC_PLAYLIST_RESPONSE)
        
        assert playlist.name == MOCK_SUBSONIC_PLAYLIST_RESPONSE.get('name')
        assert playlist.description == MOCK_SUBSONIC_PLAYLIST_RESPONSE.get('comment')
        assert playlist.is_public == MOCK_SUBSONIC_PLAYLIST_RESPONSE.get('public')
        assert playlist.author_name == MOCK_SUBSONIC_PLAYLIST_RESPONSE.get('owner')
        assert playlist.service_id == MOCK_SUBSONIC_PLAYLIST_RESPONSE.get('id')
        assert playlist.service_name == 'subsonic'
        assert playlist.service_data == MOCK_SUBSONIC_PLAYLIST_RESPONSE
        assert playlist.tracks == []

    def test_data_cannot_be_none(self, subsonic_mapper: SubsonicMapper):
        with pytest.raises(ValueError):
            subsonic_mapper.map_playlist(None)

class TestTrackMapping:
    def test_map_track(self, subsonic_mapper: SubsonicMapper):
        track = subsonic_mapper.map_track(MOCK_SUBSONIC_TRACK_RESPONSE)

        assert track.title == MOCK_SUBSONIC_TRACK_RESPONSE.get('title')
        assert track.album_name == MOCK_SUBSONIC_TRACK_RESPONSE.get('album')
        assert track.primary_artist == MOCK_SUBSONIC_TRACK_RESPONSE.get('artist')
        assert track.additional_artists == []
        assert track.duration_seconds == MOCK_SUBSONIC_TRACK_RESPONSE.get('duration')
        assert track.track_number == MOCK_SUBSONIC_TRACK_RESPONSE.get('track')
        assert track.release_year == MOCK_SUBSONIC_TRACK_RESPONSE.get('year')
        assert track.isrc == MOCK_SUBSONIC_TRACK_RESPONSE.get('isrc')
        assert track.service_id == MOCK_SUBSONIC_TRACK_RESPONSE.get('id')
        assert track.service_name == 'subsonic'
        assert track.service_data == MOCK_SUBSONIC_TRACK_RESPONSE

    def test_data_cannot_be_none(self, subsonic_mapper: SubsonicMapper):
        with pytest.raises(ValueError):
            subsonic_mapper.map_track(None)