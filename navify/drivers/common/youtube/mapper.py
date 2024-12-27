from navify.drivers import ServiceMapper
from navify.models import Playlist, Track

class YouTubeMapper(ServiceMapper):
    """Maps Youtube API DTOs to internal models."""

    def map_playlist(self, data: dict) -> 'Playlist':  
        pass

    def map_track(self, data: dict) -> 'Track':
        pass