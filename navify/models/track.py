from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Track:
    """Represents a single track."""

    title: str = field(default=None)
    """Title of the track."""
    
    album_name: Optional[str] = field(default=None)
    """Name of the album containing the track."""

    primary_artist: Optional[str] = field(default=None)
    """Primary (album) artist for the track."""

    additional_artists: List[str] = field(default_factory=list)
    """Additional artist names for the track."""

    duration_seconds: Optional[int] = field(default=None)
    """Duration of the track in seconds."""

    track_number: Optional[int] = field(default=None)
    """Track number on the album."""

    release_year: Optional[int] = field(default=None)
    """Year the track was released."""

    isrc: Optional[str] = field(default=None)
    """International Standard Recording Code for the track."""

    musicbrainz_id: Optional[str] = field(default=None)
    """MusicBrainz ID for the track."""
    
    service_id: Optional[str] = field(default=None)
    """Source-service specific ID for the track."""

    service_name: str = field(default='unknown')
    """Source service for the track."""

    service_data: Optional[dict] = field(default=None)
    """Raw JSON response data from the source service."""

    def __str__(self) -> str:
        return f"{self.track_number}. - {self.primary_artist} - {self.title}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: 'Track') -> bool:
        return self.service_id == other.service_id and self.service_name == other.service_name
    
    @classmethod
    def from_subsonic_json(cls, data: dict) -> 'Track':
        """Create a Track instance from a Subsonic API response."""
        
        service_id = data.get('id')
        title = data.get('title')
        album_name = data.get('album')
        primary_artist = data.get('artist')
        duration_seconds = int(data.get('duration')) if data.get('duration') else None
        track_number = int(data.get('track')) if data.get('track') else None
        release_year = int(data.get('year')) if data.get('year') else None
        musicbrainz_id = data.get('musicBrainzId')
        
        return cls(
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

    @classmethod
    def from_spotify_json(cls, data: dict) -> 'Track':
        """Create a Track instance from a Spotify API response."""
        
        service_id = data.get('id')
        title = data.get('name')
        album_name = data.get('album').get('name')
        primary_artist = data.get('artists')[0].get('name')
        additional_artists = [artist.get('name') for artist in data.get('artists')[1:]]
        duration_seconds = int(data.get('duration_ms') / 1000) if data.get('duration_ms') else None
        track_number = int(data.get('track_number')) if data.get('track_number') else None
        release_year = int(data.get('album').get('release_date')[:4]) if data.get('album').get('release_date') else None
        isrc = data.get('external_ids').get('isrc') if data.get('external_ids') else None
        
        return cls(
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