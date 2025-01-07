import json
import pytest

MOCK_YOUTUBE_TRACK_RESPONSE = None
with open('tests/mock/youtube_track.json', 'r') as f:
    MOCK_YOUTUBE_TRACK_RESPONSE = json.load(f)

MOCK_YOUTUBE_PLAYLIST_RESPONSE = None
with open('tests/mock/youtube_playlist.json', 'r') as f:
    MOCK_YOUTUBE_PLAYLIST_RESPONSE = json.load(f)

MOCK_YOUTUBE_SEARCH_RESPONSE = None
with open('tests/mock/youtube_search.json', 'r') as f:
    MOCK_YOUTUBE_SEARCH_RESPONSE = json.load(f)

from tunesynctool.drivers.common.youtube import YouTubeMapper

@pytest.fixture
def youtube_mapper():
    return YouTubeMapper()

class TestPlaylistMapping:
    def test_data_cannot_be_none(self, youtube_mapper: YouTubeMapper):
        with pytest.raises(ValueError):
            youtube_mapper.map_playlist(None)

    def test_map_playlist(self, youtube_mapper: YouTubeMapper):
        playlist = youtube_mapper.map_playlist(MOCK_YOUTUBE_PLAYLIST_RESPONSE)

        assert playlist.name == MOCK_YOUTUBE_PLAYLIST_RESPONSE['title']
        assert playlist.description == MOCK_YOUTUBE_PLAYLIST_RESPONSE['description']
        assert playlist.service_id == MOCK_YOUTUBE_PLAYLIST_RESPONSE['id']
        assert playlist.service_data == MOCK_YOUTUBE_PLAYLIST_RESPONSE
        assert playlist.is_public == (MOCK_YOUTUBE_PLAYLIST_RESPONSE['privacy'] == 'PUBLIC')
        assert playlist.service_name == 'youtube'
        assert playlist.author_name == None
        assert playlist.tracks == []

class TestTrackMapping:
    def test_map_track(self, youtube_mapper: YouTubeMapper):
        track = youtube_mapper.map_track(
            data=MOCK_YOUTUBE_TRACK_RESPONSE,
            additional_data=MOCK_YOUTUBE_SEARCH_RESPONSE
        )
        
        assert track.title == MOCK_YOUTUBE_TRACK_RESPONSE['videoDetails']['title']
        assert track.album_name == MOCK_YOUTUBE_SEARCH_RESPONSE['album']['name']
        assert track.primary_artist == MOCK_YOUTUBE_SEARCH_RESPONSE['artists'][0]['name']
        assert track.additional_artists == [artist['name'] for artist in MOCK_YOUTUBE_SEARCH_RESPONSE['artists'][1:]]
        assert track.duration_seconds == int(MOCK_YOUTUBE_TRACK_RESPONSE['videoDetails']['lengthSeconds'])
        assert track.track_number == None
        assert track.release_year == MOCK_YOUTUBE_SEARCH_RESPONSE['year']
        assert track.isrc == None
        assert track.service_id == MOCK_YOUTUBE_TRACK_RESPONSE['videoDetails']['videoId']
        
        assert track.service_name == 'youtube'
        assert track.service_data == {
            'track': MOCK_YOUTUBE_TRACK_RESPONSE,
            'search': MOCK_YOUTUBE_SEARCH_RESPONSE
        }

    def test_data_cannot_be_none(self, youtube_mapper: YouTubeMapper):
        with pytest.raises(ValueError):
            youtube_mapper.map_track(
                data=None,
                additional_data=None
            )

        with pytest.raises(ValueError):
            youtube_mapper.map_track(
                data={},
                additional_data=None
            )

        with pytest.raises(ValueError):
            youtube_mapper.map_track(
                data=None,
                additional_data={}
            )