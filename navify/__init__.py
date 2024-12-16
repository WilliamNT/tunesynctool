from .models.configuration import Configuration

config = Configuration.from_env()

from .drivers.spotify import SpotifyDriver
spotify = SpotifyDriver(config)

from .drivers.subsonic import SubsonicDriver
subsonic = SubsonicDriver(config)

from .models import Playlist, Track
