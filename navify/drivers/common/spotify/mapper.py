from navify.drivers import ServiceMapper
from navify.models import Playlist, Track

class SpotifyMapper(ServiceMapper):
    """Maps Spotify API DTOs to internal models."""

    def map_playlist(self, data: dict) -> 'Playlist':  
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
              
        service_id = data.get('id', None)
        name = data.get('name', None)
        description = data.get('description', None)
        is_public = data.get('public', False)
        author_name = data.get('owner', {}).get('display_name', None)
        
        return Playlist(
            service_id=service_id,
            service_name='spotify',
            name=name,
            description=description,
            is_public=is_public,
            author_name=author_name,
            service_data=data
        )
    
    def map_track(self, data: dict) -> 'Track':
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
        
        _raw_artists = data.get('artists', [])
        
        service_id = data.get('id', None)
        title = data.get('name', None)
        album_name = data.get('album', {}).get('name', None)
        primary_artist = _raw_artists[0].get('name', None) if len(_raw_artists) > 0 else None
        duration_seconds = int(data.get('duration_ms', None) / 1000) if data.get('duration_ms', None) else None
        track_number = int(data.get('track_number', None)) if data.get('track_number', None) else None
        release_year = int(data.get('album', {}).get('release_date', None)[:4]) if data.get('album', {}).get('release_date', None) else None
        isrc = data.get('external_ids', {}).get('isrc', None) if data.get('external_ids', None) else None
        
        additional_artists = []
        if len(_raw_artists) > 1:
            additional_artists = [artist.get('name', None) for artist in _raw_artists[1:]]
        
        return Track(
            title=title,
            album_name=album_name,
            primary_artist=primary_artist,
            additional_artists=additional_artists,
            duration_seconds=duration_seconds,
            track_number=track_number,
            release_year=release_year,
            isrc=isrc,
            service_id=service_id,
            service_name='spotify',
            service_data=data
        )