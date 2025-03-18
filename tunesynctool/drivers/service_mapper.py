from abc import ABC, abstractmethod
from typing import List

from tunesynctool.models import Playlist, Track

class ServiceMapper(ABC):
    """
    Defines the interface for a service-specific mapper.
    Responsible for mapping API DTOs to their respective internal models.
    Do not use directly; subclass this class to implement a custom mapper.
    """

    @abstractmethod
    def map_playlist(self, data: dict) -> Playlist:
        """Map a playlist DTO to a Playlist model."""
        raise NotImplementedError()

    @abstractmethod
    def map_track(self, data: dict) -> Track:
        """Map a track DTO to a Track model."""
        raise NotImplementedError()