from typing import List

from tunesynctool.drivers import ServiceMapper
from tunesynctool.models import Playlist, Track

class DeezerMapper(ServiceMapper):
    """Maps Deezer API DTOs to internal models."""

    def map_playlist(self, data: dict) -> Playlist:  
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
              
        service_id = data.get('id', None)
        name = data.get('title', None)
        description = data.get('description', None)
        is_public = data.get('public', False)
        author_name = data.get('creator', {}).get('name', None)
        
        return Playlist(
            service_id=service_id,
            service_name='deezer',
            name=name,
            description=description,
            is_public=is_public,
            author_name=author_name,
            service_data=data
        )
    
    def map_track(self, data: dict) -> Track:
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
        
        _raw_artists: List[dict] = data.get('contributors', [])

        service_id = data.get('id', None)
        title = data.get('title', None)
        album_name = data.get('album', {}).get('title', None)
        primary_artist = data.get('artist', {}).get('name', None)
        duration_seconds = int(data.get('duration')) if data.get('duration', None) else None
        release_year = int(data.get('release_date')[:4]) if data.get('release_date', None) else None
        isrc = data.get('isrc')
        track_number = int(data.get('track_position')) if data.get('track_position', None) else None
        
        additional_artists = []

        if len(_raw_artists) > 1:
            for artist in _raw_artists:
                if artist.get('role', None) != 'Main':
                    artist_name = artist.get('name', None)

                    if artist_name:
                        additional_artists.append(artist_name)
        
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
            service_name='deezer',
            service_data=data
        )