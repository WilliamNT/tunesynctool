from typing import Optional

from navify.cli.utils.driver import get_driver_by_name, SUPPORTED_PROVIDERS
from navify.drivers import ServiceDriver
from navify.features import TrackMatcher

from click import command, option, Choice, echo, argument, pass_obj, Context, UsageError, style
from tqdm import tqdm

@command()
@pass_obj
@option('--from', 'from_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The provider to copy the playlist from.')
@option('--to', 'to_provider', type=Choice(SUPPORTED_PROVIDERS), required=True, help='The target provider to copy the playlist to.')
@argument('playlist_id', type=str, required=True)
def transfer(ctx: Optional[dict], from_provider: str, to_provider: str, playlist_id: str):
    """Transfers a playlist from one provider to another."""

    try:
        source_driver: ServiceDriver = get_driver_by_name(from_provider)(ctx['config'])
        target_driver: ServiceDriver = get_driver_by_name(to_provider)(ctx['config'])
    except ValueError as e:
        raise UsageError(e)
    
    echo(style('Looking up playlist...', fg='blue'))

    source_playlist = source_driver.get_playlist(playlist_id)
    echo(style(f"Found playlist: {source_playlist}", fg='green'))

    source_tracks = source_driver.get_playlist_tracks(source_playlist.service_id)
    echo(style(f"Found {len(source_tracks)} tracks in the playlist"))

    matcher = TrackMatcher(target_driver)
    matched_tracks = []

    for track in tqdm(source_tracks, desc='Matching tracks'):
        matched_track = matcher.find_match(track)
        
        if matched_track:
            matched_tracks.append(matched_track)
            tqdm.write(style(f"Found match: \"{matched_track}\"", fg='green'))
        else:
            tqdm.write(style(f"No match found for \"{track}\"", fg='yellow'))

    target_playlist = target_driver.create_playlist(source_playlist.name)

    target_driver.add_tracks_to_playlist(
        playlist_id=target_playlist.service_id,
        track_ids=[track.service_id for track in matched_tracks],
    )
    echo(style(f"Added {len(matched_tracks)} tracks to the playlist", fg='green'))
    echo(style(f"Playlist transfer complete!", fg='green'))
