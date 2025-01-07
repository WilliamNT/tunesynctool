import pytest

from tunesynctool.models import Playlist

class TestPlaylist:
    def test_playlist_str(self):
        playlist = Playlist(name='Test Playlist', author_name='Test Author')
        assert str(playlist) == 'Test Playlist by Test Author'

    def test_playlist_repr(self):
        playlist = Playlist(name='Test Playlist', author_name='Test Author')
        assert repr(playlist) == 'Test Playlist by Test Author'

    def test_playlist_equals(self):
        playlist1 = Playlist(service_id='1', service_name='spotify')
        playlist2 = Playlist(service_id='1', service_name='spotify')
        assert playlist1 == playlist2

    def test_playlist_dont_equal(self):
        playlist1 = Playlist(service_id='1', service_name='spotify')
        playlist2 = Playlist(service_id='2', service_name='spotify')
        assert playlist1 != playlist2

        playlist1 = Playlist(service_id='1', service_name='one')
        playlist2 = Playlist(service_id='1', service_name='another')
        assert playlist1 != playlist2

    def test_fallback_values(self):
        playlist = Playlist()

        assert playlist.name == 'Untitled Playlist [@tunesynctool]'
        assert playlist.author_name == None
        assert playlist.description == None
        assert playlist.is_public == False
        assert playlist.tracks == []
        assert playlist.service_id == None
        assert playlist.service_name == 'unknown'
        assert playlist.service_data == {}