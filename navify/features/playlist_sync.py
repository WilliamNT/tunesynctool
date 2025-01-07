from typing import List, Optional

from navify.drivers import ServiceDriver
from navify.models import Track
from navify.features.track_matcher import TrackMatcher

class PlaylistSynchronizer:
    """
    Attempts to synchronize a playlist between two services.
    """

    def __init__(self, source_driver: ServiceDriver, target_driver: ServiceDriver):
        """
        Initializes a new instance of PlaylistSynchronizer.

        :param source_driver: The driver for the source service.
        :param target_driver: The driver for the target service.
        """

        self.__source = source_driver
        self.__target = target_driver
        self.__target_matcher = TrackMatcher(target_driver)
    
    def find_missing_tracks(self, source_playlist_tracks: List[Track], target_playlist_tracks: List[Track]) -> List[Track]:
        """
        Returns a list of tracks that are present in the source playlist but not in the target playlist.

        :param source_playlist_tracks: The tracks in the source playlist.
        :param target_playlist_tracks: The tracks in the target playlist.
        :return: A list of tracks that are present in the source playlist but not in the target playlist.
        """

        tracks_that_are_not_in_target_but_are_in_source = []
        processed_target_tracks = set()

        for source_track in source_playlist_tracks:
            match_found = False

            for target_track in target_playlist_tracks:
                if target_track in processed_target_tracks:
                    continue

                if source_track.matches(target_track):
                    match_found = True
                    processed_target_tracks.add(target_track)
                    break

            if not match_found:
                tracks_that_are_not_in_target_but_are_in_source.append(source_track)

        return tracks_that_are_not_in_target_but_are_in_source
    
    def sync(self, source_playlist_id: str, target_playlist_id: str) -> None:
        """
        Synchronizes the source playlist with the target playlist.

        :param source_playlist_id: The ID of the source playlist.
        :param target_playlist_id: The ID of the target playlist.
        :return: None
        """

        source_playlist_tracks  = self.__source.get_playlist_tracks(
            playlist_id=source_playlist_id
        )
        target_playlist_tracks = self.__target.get_playlist_tracks(
            playlist_id=target_playlist_id
        )

        missing_tracks = self.find_missing_tracks(
            source_playlist_tracks=source_playlist_tracks,
            target_playlist_tracks=target_playlist_tracks
        )
        
        matched_tracks = []
        for track in missing_tracks:
            matched_track = self.__target_matcher.find_match(
                track=track
            )

            if matched_track:
                matched_tracks.append(matched_track)
        
        self.__target.add_tracks_to_playlist(
            playlist_id=target_playlist_id,
            track_ids=[track.service_id for track in matched_tracks]
        )