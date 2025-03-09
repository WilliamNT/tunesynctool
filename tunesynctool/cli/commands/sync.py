from typing import Optional, List

from tunesynctool.cli.utils.driver import get_driver_by_name, SUPPORTED_PROVIDERS
from tunesynctool.drivers import ServiceDriver
from tunesynctool.features import PlaylistSynchronizer, TrackMatcher
from tunesynctool.models import Track
from tunesynctool.exceptions import PlaylistNotFoundException

from click import command, option, Choice, echo, argument, pass_obj, UsageError, style, Abort
from tqdm import tqdm

COMMON_MATCH_ISSUE_REASON = 'This is likely caused by tracks not being available on the target service, they lack metadata or the matching algorithm was unsuccessful in finding them.'

def list_tracks(tracks: List[Track], color: str = 'yellow') -> None:
    for track in tracks:
        echo(style(track, fg=color))

@command()
@pass_obj
@option('--from', 'from_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The provider to sync the playlist from.')
@option('--from-playlist', 'from_playlist_id', type=str, required=True, help='ID of the playlist on the source provider you want to sync from.')
@option('--to', 'to_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The target provider to sync the playlist to.')
@option('--to-playlist', 'to_playlist_id', type=str, required=True, help='ID of the playlist on the target provider you want to sync to.')
@option('--preview', 'is_preview', is_flag=True, show_default=True, default=False, help='Preview the sync without actually touching the target service.')
@option('--diff', 'show_diff', is_flag=True, show_default=True, default=False, help='Show the difference between the source and target playlists.')
@option('--misses', 'show_misses', is_flag=True, show_default=True, default=False, help='Show the tracks that couldn\'t be matched.')
@option('--limit', 'limit', type=int, default=0, show_default=True, help='Limit the number of tracks to transfer. 0 or smaller means no limit. Default is 100. There is no upper limit, but be aware that some services may rate limit you.')
def sync(
    ctx: Optional[dict],
    from_provider: str,
    from_playlist_id: str,
    to_provider: str,
    to_playlist_id: str,
    is_preview: bool,
    show_diff: bool,
    show_misses: bool,
    limit: int
    ):
    """Synchronizes a playlist from one service to another. Updates the target playlist with the source playlist's missing tracks."""

    try:
        source_driver: ServiceDriver = get_driver_by_name(from_provider)(ctx['config'])
        target_driver: ServiceDriver = get_driver_by_name(to_provider)(ctx['config'])
    except ValueError as e:
        raise UsageError(e)
    
    echo(style('Looking up playlists...', fg='blue'))
    
    try:
        source_playlist = source_driver.get_playlist(from_playlist_id)
        target_playlist = target_driver.get_playlist(to_playlist_id)
        echo(style(f"Found source playlist \"{target_playlist}\" and target playlist \"{source_playlist}\"", fg='blue'))
    except PlaylistNotFoundException:
        raise UsageError('One or more playlist IDs are invalid.')

    source_playlist_tracks = source_driver.get_playlist_tracks(
        playlist_id=from_playlist_id,
        limit=limit
    )
    target_playlist_tracks = target_driver.get_playlist_tracks(
        playlist_id=to_playlist_id,
        limit=0,
    )

    synchronizer = PlaylistSynchronizer(
        source_driver=source_driver,
        target_driver=target_driver
    )

    diff = synchronizer.find_missing_tracks(
        source_playlist_tracks=source_playlist_tracks,
        target_playlist_tracks=target_playlist_tracks
    )

    echo(style(f'Found {len(diff)} tracks that are missing from the target playlist', fg='blue'))

    if len(diff) == 0:
        echo(style('No tracks to sync, target playlist is up-to-date', fg='green'))
        return

    if show_diff:
        for d in diff:
            echo(style(d, fg='yellow'))
    
    matcher = TrackMatcher(target_driver)

    matched_tracks = []
    for track in tqdm(diff, desc='Matching tracks'):
        matched_track = matcher.find_match(track)

        if matched_track:
            matched_tracks.append(matched_track)
            tqdm.write(style(f"Success: Found match: \"{track}\" --> \"{matched_track}\"", fg='green'))
        else:
            tqdm.write(style(f"Fail: No result for \"{track}\"", fg='yellow'))

    echo(style(f"Found {len(matched_tracks)} matches in total", fg='blue' if len(matched_tracks) > 0 else 'red'))

    if len(matched_tracks) != 0:
        echo(style("Updating target playlist...", fg='blue'))

        if is_preview:
            echo(style("Preview mode is enabled, skipping actual update", fg='blue'))
        else:
            try:
                target_driver.add_tracks_to_playlist(
                    playlist_id=to_playlist_id,
                    track_ids=[track.service_id for track in matched_tracks],
                )
                echo(style("Target playlist updated", fg='green'))
            except Exception as e:
                raise Abort()

    else:
        echo(style("Warning: Can't update target playlist because no matches were found.", fg='yellow'))
        echo(style(COMMON_MATCH_ISSUE_REASON, fg='yellow'))

        if show_misses:
            list_tracks(diff, color='yellow')
        else:
            echo(style('Re-run the command with the --misses flag to automatically list the missing tracks.', fg='yellow'))

        echo(style('Sync unsuccessful', fg='red'))
        return
    
    if len(matched_tracks) != len(diff):
        echo(style(f"Warning: Only {len(matched_tracks)} out of {len(diff)} tracks were matched (the rest couldn't be identified)", fg='yellow'))
        echo(style(COMMON_MATCH_ISSUE_REASON, fg='yellow'))

        if show_misses:
            list_tracks([track for track in diff if track not in matched_tracks], color='yellow')
        else:
            echo(style('Re-run this command with the --misses flag to automatically list the missing tracks.', fg='yellow'))

        echo(style('Sync was only partially successful', fg='yellow'))
        return

    echo(style(f"Sync complete!", fg='green'))