from .models.configuration import Configuration

from .drivers import SubsonicDriver, SpotifyDriver, DeezerDriver, YouTubeDriver

from .models import Playlist, Track

from .features import TrackMatcher, PlaylistSynchronizer, AsyncTrackMatcher

import logging

logger = logging.getLogger(__name__)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)