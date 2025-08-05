from dataclasses import dataclass, field
from typing import List, Optional, Self
import base64
import json

from tunesynctool.utilities import clean_str, calculate_str_similarity, calculate_int_closeness

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

    service_data: Optional[dict] = field(default_factory=dict)
    """Raw JSON response data from the source service."""

    def __str__(self) -> str:
        return f"{self.track_number}. - {self.primary_artist} - {self.title}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: Optional[Self]) -> bool:
        if not other:
            return False
        
        return self.service_id == other.service_id and self.service_name == other.service_name
    
    def __hash__(self):
        return hash((self.service_id, self.service_name))

    def matches(self, other: Optional[Self], threshold: float = 0.75) -> bool:
        """
        Compares two tracks for equality, regardless of their source service.
        For primitive matching, use the __eq__ method (== operator).

        This is not 100% accurate, but it's good enough in most cases.
        """

        return self.similarity(other) >= threshold
    
    def similarity(self, other: Optional[Self]) -> float:
        """
        Approximates the similarity between two tracks.

        This is not 100% accurate, but it's good enough in most cases.

        :param other: The other track to compare to.
        :return: A float value representing the similarity between 0.0 and 1.0.
        """

        if not other:
            return 0.0
        elif (self.isrc and other.isrc) and self.isrc == other.isrc:
            return 1.0
        elif (self.musicbrainz_id and other.musicbrainz_id) and self.musicbrainz_id == other.musicbrainz_id:
            return 1.0
        
        title_similarity = calculate_str_similarity(clean_str(self.title), clean_str(other.title))
        artist_similarity = calculate_str_similarity(clean_str(self.primary_artist), clean_str(other.primary_artist))
        
        # if title_similarity < 0.65 or artist_similarity < 0.6:
        #     return 0.0

        weights = {
            'title': 4.0,
            'artist': 3.0,
            'album': 1.25 if self.album_name and other.album_name else 0.75,
            'duration': 0.75,
            'track': 0.5 if self.track_number and other.track_number else 0,
            'year': 0.5 if self.track_number and other.track_number else 0,
        }

        variables = [
            title_similarity * weights['title'],
            artist_similarity * weights['artist'],
            calculate_str_similarity(clean_str(self.album_name), clean_str(other.album_name)) * weights['album'],
            calculate_int_closeness(self.duration_seconds, other.duration_seconds) * weights['duration'],
            calculate_int_closeness(self.track_number, other.track_number) * weights['track'],
            calculate_int_closeness(self.release_year, other.release_year) * weights['year'],
        ]

        similarity_ratio = round(sum(variables) / sum(weights.values()), 2)

        return similarity_ratio
    
    def serialize(self) -> dict:
        """
        Maps the object to a dict.
        """

        service_data = base64.b64encode(json.dumps(self.service_data).encode("utf-8"))

        return {
            "title": self.title,
            "album_name": self.album_name,
            "primary_artist": self.primary_artist,
            "additional_artists": self.additional_artists,
            "duration_seconds": self.duration_seconds,
            "track_number": self.track_number,
            "release_year": self.release_year,
            "isrc": self.isrc,
            "musicbrainz_id": self.musicbrainz_id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_data": service_data.decode("utf-8")
        }
    
    @staticmethod
    def deserialize(raw_json: dict) -> Self:
        decoded_service_data = None
        if raw_json.get("service_data"):
            decoded_service_data = base64.b64decode(raw_json.get("service_data"))
            decoded_service_data = decoded_service_data.decode("utf-8")
            decoded_service_data = json.loads(decoded_service_data)

        return Track(
            title=raw_json.get("title"),
            album_name=raw_json.get("album_name"),
            primary_artist=raw_json.get("primary_artist"),
            additional_artists=raw_json.get("additional_artists", []),
            duration_seconds=int(raw_json.get("duration_seconds")) if raw_json.get("duration_seconds") else None,
            track_number=int(raw_json.get("track_number")) if raw_json.get("track_number") else None,
            release_year=int(raw_json.get("release_year")) if raw_json.get("release_year") else None,
            isrc=raw_json.get("isrc"),
            musicbrainz_id=raw_json.get("musicbrainz_id"),
            service_id=raw_json.get("service_id"),
            service_name=raw_json.get("service_name"),
            service_data=decoded_service_data
        )