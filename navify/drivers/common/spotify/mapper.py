from navify.drivers import ServiceMapper
from navify.models import Playlist, Track

class SpotifyMapper(ServiceMapper):
    """Maps Spotify API DTOs to internal models."""

    def map_playlist(self, data: dict) -> 'Playlist':        
        service_id = data.get('id')
        name = data.get('name')
        description = data.get('description')
        is_public = data.get('public', False)
        author_name = data.get('owner').get('display_name')
        
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
        service_id = data.get('id')
        title = data.get('name')
        album_name = data.get('album').get('name')
        primary_artist = data.get('artists')[0].get('name')
        additional_artists = [artist.get('name') for artist in data.get('artists')[1:]]
        duration_seconds = int(data.get('duration_ms') / 1000) if data.get('duration_ms') else None
        track_number = int(data.get('track_number')) if data.get('track_number') else None
        release_year = int(data.get('album').get('release_date')[:4]) if data.get('album').get('release_date') else None
        isrc = data.get('external_ids').get('isrc') if data.get('external_ids') else None
        
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