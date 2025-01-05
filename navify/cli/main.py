import click

from .commands import transfer

from navify.models.configuration import Configuration

@click.group()
@click.option('--spotify-client-id', 'spotify_client_id', help='Spotify client ID.')
@click.option('--spotify-client-secret', 'spotify_client_secret', help='Spotify client secret.')
@click.option('--spotify-redirect-uri', 'spotify_redirect_uri', default='http://localhost:8888/callback', help='Spotify redirect URI.')
@click.option('--subsonic-base-url', 'subsonic_base_url', help='Base URL for the Subsonic server.')
@click.option('--subsonic-port', 'subsonic_port', type=int, help='Port for the Subsonic server.')
@click.option('--subsonic-username', 'subsonic_username', help='Username for the Subsonic server.')
@click.option('--subsonic-password', 'subsonic_password', help='Password for the Subsonic server.')
@click.option('--deezer-arl', 'deezer_arl', help='Deezer ARL token.')
@click.option('--youtube-request-headers', 'youtube_request_headers', help='YouTube request headers.')
@click.pass_context
def cli(ctx: click.Context, spotify_client_id, spotify_client_secret, spotify_redirect_uri, subsonic_base_url, subsonic_port, subsonic_username, subsonic_password, deezer_arl, youtube_request_headers):
    """Entry point for the CLI."""

    ctx.ensure_object(dict)

    ctx.obj['config'] = Configuration(
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret,
        spotify_redirect_uri=spotify_redirect_uri,
        subsonic_base_url=subsonic_base_url,
        subsonic_port=subsonic_port,
        subsonic_username=subsonic_username,
        subsonic_password=subsonic_password,
        deezer_arl=deezer_arl,
        youtube_request_headers=youtube_request_headers,
    )

cli.add_command(transfer.transfer)

if __name__ == '__main__':
    cli()