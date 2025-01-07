from tunesynctool.drivers import ServiceMapper
from tunesynctool.models import Playlist, Track

class SubsonicMapper(ServiceMapper):
    """Maps Subsonic API DTOs to internal models."""

    def map_playlist(self, data: dict) -> 'Playlist':
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')

        service_id = data.get('id')
        name = data.get('name')
        description = data.get('comment')
        is_public = data.get('public', False)
        author_name = data.get('owner')
        
        return Playlist(
            service_id=service_id,
            service_name='subsonic',
            name=name,
            description=description,
            is_public=is_public,
            author_name=author_name,
            service_data=data
        )
    
    def map_track(self, data: dict) -> 'Track':
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
        
        service_id = data.get('id')
        title = data.get('title')
        album_name = data.get('album')
        primary_artist = data.get('artist')
        duration_seconds = int(data.get('duration')) if data.get('duration') else None
        track_number = int(data.get('track')) if data.get('track') else None
        release_year = int(data.get('year')) if data.get('year') else None
        musicbrainz_id = data.get('musicBrainzId')
        
        return Track(
            title=title,
            album_name=album_name,
            primary_artist=primary_artist,
            duration_seconds=duration_seconds,
            track_number=track_number,
            release_year=release_year,
            musicbrainz_id=musicbrainz_id,
            service_id=service_id,
            service_name='subsonic',
            service_data=data
        )