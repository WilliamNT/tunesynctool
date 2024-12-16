class PlaylistNotFoundException(Exception):
    def __init__(self, message="Playlist not found."):
        super().__init__(message)

class TrackNotFoundException(Exception):
    def __init__(self, message="Track not found."):
        super().__init__(message)

class ServiceDriverException(Exception):
    def __init__(self, message="Unknown driver error."):
        super().__init__(message)