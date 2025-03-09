from typing import Optional

from tunesynctool.cli.utils.driver import get_driver_by_name, SUPPORTED_PROVIDERS
from tunesynctool.drivers import ServiceDriver
from tunesynctool.features import TrackMatcher
from tunesynctool.exceptions import PlaylistNotFoundException

from click import command, option, Choice, echo, argument, pass_obj, UsageError, style, Abort
from tqdm import tqdm

@command()
@pass_obj
@option('--from', 'from_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The provider to copy the playlist from.')
@option('--to', 'to_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The target provider to copy the playlist to.')
@option('--preview', 'is_preview', is_flag=True, show_default=True, default=False, help='Preview the transfer without actually touching the target service.')
@option('--limit', 'limit', type=int, default=0, show_default=True, help='Limit the number of tracks to transfer. 0 or smaller means no limit. Default is 100. There is no upper limit, but be aware that some services may rate limit you.')
@argument('playlist_id', type=str, required=True)
def transfer(
    ctx: Optional[dict],
    from_provider: str,
    to_provider: str,
    playlist_id: str,
    is_preview: bool,
    limit: int
    ):
    """Transfers a playlist from one provider to another."""

    try:
        source_driver: ServiceDriver = get_driver_by_name(from_provider)(ctx['config'])
        target_driver: ServiceDriver = get_driver_by_name(to_provider)(ctx['config'])
    except ValueError as e:
        raise UsageError(e)
    
    echo(style('Looking up playlist...', fg='blue'))

    try:
        source_playlist = source_driver.get_playlist(playlist_id)
        echo(style(f"Found playlist: {source_playlist}", fg='green'))
    except PlaylistNotFoundException:
        raise UsageError('Source playlist ID is invalid.')
    
    source_tracks = source_driver.get_playlist_tracks(
        playlist_id=source_playlist.service_id,
        limit=limit
    )

    matcher = TrackMatcher(target_driver)
    matched_tracks = []

    for track in tqdm(source_tracks, desc='Matching tracks'):
        matched_track = matcher.find_match(track)
        
        if matched_track:
            matched_tracks.append(matched_track)
            tqdm.write(style(f"Success: Found match: \"{track}\" --> \"{matched_track}\"", fg='green'))
        else:
            tqdm.write(style(f"Fail: No result for \"{track}\"", fg='yellow'))

    echo(style(f"Found {len(matched_tracks)} matches in total", fg='blue' if len(matched_tracks) > 0 else 'red'))

    if is_preview:
        echo(style("Preview transfer complete", fg='green'))
        return
    
    try:
        target_playlist = target_driver.create_playlist(source_playlist.name)

        target_driver.add_tracks_to_playlist(
            playlist_id=target_playlist.service_id,
            track_ids=[track.service_id for track in matched_tracks],
        )
    except Exception as e:
        echo(style(f"Failed to transfer playlist: {e}", fg='red'))
        raise Abort()
    
    echo(style(f"Playlist transfer complete!", fg='green'))
