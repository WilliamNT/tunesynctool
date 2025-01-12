class PlaylistNotFoundException(Exception):
    """Indicates that a playlist could not be found or retrieved for technical reasons from the streaming service."""
    
    def __init__(self, message="Playlist not found."):
        super().__init__(message)

class TrackNotFoundException(Exception):
    """Indicates that a track could not be found or retrieved for technical reasons from the streaming service."""
    
    def __init__(self, message="Track not found."):
        super().__init__(message)

class ServiceDriverException(Exception):
    """Should be raised when an error occurs in the driver that is not related to the streaming service or no better exception exists."""
    
    def __init__(self, message="Unknown driver error."):
        super().__init__(message)

class UnsupportedFeatureException(Exception):
    """Should be raised when a feature is not supported by the streaming service and no easy workaround is possible."""
    
    def __init__(self, message="Feature is not supported by the streaming service."):
        super().__init__(message)