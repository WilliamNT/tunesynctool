import json
import pytest

MOCK_SPOTIFY_TRACK_RESPONSE = None
with open('tests/mock/spotify_track.json', 'r') as f:
    MOCK_SPOTIFY_TRACK_RESPONSE = json.load(f)

MOCK_SPOTIFY_PLAYLIST_RESPONSE = None
with open('tests/mock/spotify_playlist.json', 'r') as f:
    MOCK_SPOTIFY_PLAYLIST_RESPONSE = json.load(f)

from tunesynctool.drivers.common.spotify import SpotifyMapper

@pytest.fixture
def spotify_mapper():
    return SpotifyMapper()

class TestPlaylistMapping:
    def test_map_playlist(self, spotify_mapper: SpotifyMapper):
        playlist = spotify_mapper.map_playlist(MOCK_SPOTIFY_PLAYLIST_RESPONSE)
        
        assert playlist.name == MOCK_SPOTIFY_PLAYLIST_RESPONSE.get('name')
        assert playlist.description == MOCK_SPOTIFY_PLAYLIST_RESPONSE.get('description')
        assert playlist.is_public == MOCK_SPOTIFY_PLAYLIST_RESPONSE.get('public')
        assert playlist.author_name == MOCK_SPOTIFY_PLAYLIST_RESPONSE.get('owner').get('display_name')
        assert playlist.service_id == MOCK_SPOTIFY_PLAYLIST_RESPONSE.get('id')
        assert playlist.service_name == 'spotify'
        assert playlist.service_data == MOCK_SPOTIFY_PLAYLIST_RESPONSE
        assert playlist.tracks == []

    def test_data_cannot_be_none(self, spotify_mapper: SpotifyMapper):
        with pytest.raises(ValueError):
            spotify_mapper.map_playlist(None)

class TestTrackMapping:
    def test_map_track(self, spotify_mapper: SpotifyMapper):
        track = spotify_mapper.map_track(MOCK_SPOTIFY_TRACK_RESPONSE)

        assert track.title == MOCK_SPOTIFY_TRACK_RESPONSE.get('name')
        assert track.album_name == MOCK_SPOTIFY_TRACK_RESPONSE.get('album').get('name')
        assert track.primary_artist == MOCK_SPOTIFY_TRACK_RESPONSE.get('artists')[0].get('name')
        assert track.additional_artists == [artist.get('name') for artist in MOCK_SPOTIFY_TRACK_RESPONSE.get('artists')[1:]]
        assert track.duration_seconds == int(MOCK_SPOTIFY_TRACK_RESPONSE.get('duration_ms') / 1000)
        assert track.track_number == MOCK_SPOTIFY_TRACK_RESPONSE.get('track_number')
        assert track.release_year == int(MOCK_SPOTIFY_TRACK_RESPONSE.get('album').get('release_date')[:4])
        assert track.isrc == MOCK_SPOTIFY_TRACK_RESPONSE.get('external_ids').get('isrc')
        assert track.service_id == MOCK_SPOTIFY_TRACK_RESPONSE.get('id')
        assert track.service_name == 'spotify'
        assert track.service_data == MOCK_SPOTIFY_TRACK_RESPONSE

    def test_data_cannot_be_none(self, spotify_mapper: SpotifyMapper):
        with pytest.raises(ValueError):
            spotify_mapper.map_track(None)