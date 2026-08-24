from tunesynctool.drivers import ServiceDriver
from tunesynctool.exceptions import TrackNotFoundException


class MockServiceDriver(ServiceDriver):
    def __init__(self, tracks, style):
        self._tracks = list(tracks)
        self.service_name = style.name
        self.supports_direct_isrc_querying = style.supports_direct_isrc_querying
        self.supports_musicbrainz_id_querying = style.supports_musicbrainz_id_querying

    def get_track(self, track_id):
        for track in self._tracks:
            if track.service_id == track_id:
                return track
        raise TrackNotFoundException()

    def get_track_by_isrc(self, isrc):
        for track in self._tracks:
            if track.isrc == isrc:
                return track
        raise TrackNotFoundException()

    def search_tracks(self, query, limit=10):
        return self._tracks[:limit]

    def get_user_playlists(self, limit=25):
        raise NotImplementedError()

    def get_playlist_tracks(self, playlist_id, limit=100):
        raise NotImplementedError()

    def create_playlist(self, name):
        raise NotImplementedError()

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        raise NotImplementedError()

    def get_random_track(self):
        raise NotImplementedError()

    def get_playlist(self, playlist_id):
        raise NotImplementedError()

    def get_saved_tracks(self, limit=10):
        raise NotImplementedError()