from navify.drivers import ServiceMapper
from navify.models import Playlist, Track

from typing import List

class YouTubeMapper(ServiceMapper):
    """Maps Youtube API DTOs to internal models."""

    def map_playlist(self, data: dict) -> 'Playlist':  
        if isinstance(data, type(None)):
            raise ValueError('Input data cannot be None')
                
        return Playlist(
            name=data.get('title', None),
            description=data.get('description', None),
            service_id=data.get('id', data.get('playlistId', None)), # Youtube uses both 'id' and 'playlistId' keys depending on the endpoint
            is_public=data.get('privacy', None) == 'PUBLIC',
            service_name='youtube',
            service_data=data
        )

    def map_track(self, data: dict, additional_data: dict = {}) -> 'Track':
        if isinstance(data, type(None)) or isinstance(additional_data, type(None)):
            raise ValueError('Input data or additional_data cannot be None')
        
        album: dict = additional_data.get('album', {})
        video_details: dict = data.get('videoDetails', {})
        _raw_artists: List[dict] = additional_data.get('artists', [])
        _artist_names = [artist.get('name', None) for artist in _raw_artists]
        
        service_id = video_details.get('videoId', None)
        title = video_details.get('title', None)

        album_name = album.get('name', None)
        primary_artist = _artist_names[0] if len(_artist_names) > 0 else None
        duration_seconds = int(video_details.get('lengthSeconds', None)) if video_details.get('lengthSeconds', None) else None
        release_year = int(additional_data.get('year')) if additional_data.get('year', None) else None
        
        track_number = None # Youtube does not provide track numbers as far as I know
        isrc = None # Youtube does not provide ISRCs as far as I know
        
        additional_artists = []
        if len(_artist_names) > 1:
            additional_artists = [artist for artist in _artist_names[1:]]
        
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
            service_name='youtube',
            service_data={
                'track': data,
                'search': additional_data
            }
        )