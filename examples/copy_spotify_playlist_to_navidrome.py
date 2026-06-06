from tunesynctool import Configuration, SpotifyDriver, SubsonicDriver, TrackMatcher

# Method 1:
# Load environment variables from a .env file
# from dotenv import load_dotenv
# load_dotenv()
# config = Configuration.from_env()

# Method 2:
# Set environment variables directly
config = Configuration(
    spotify_client_id='your-client-id',
    spotify_client_secret='your-client-secret',
    subsonic_base_url='http://localhost',
    subsonic_port=4533,
    subsonic_username='username',
    subsonic_password='password',
)

# Create the drivers
navidrome = SubsonicDriver(config) # for Navidrome
spotify = SpotifyDriver(config) # for Spotify

# Get yor Spotify playlist
spotify_playlist = spotify.get_playlist('your-playlist-id')

# Get the tracks from the playlist
spotify_tracks = spotify.get_playlist_tracks(spotify_playlist.service_id)

# Create a track matcher
matcher = TrackMatcher(
    target_driver=navidrome,
)

matched_tracks = []
for track in spotify_tracks:
    matched_track = matcher.find_match(track)

    if matched_track:
        matched_tracks.append(matched_track)

# Get or create a playlist in Navidrome
existing_playlists = navidrome.get_playlists()
navidrome_playlist = next(
    (p for p in existing_playlists if p.name == spotify_playlist.name),
    None
)

if navidrome_playlist is None:
    navidrome_playlist = navidrome.create_playlist(spotify_playlist.name)

# Determine which tracks are not already in the playlist
existing_tracks = navidrome.get_playlist_tracks(navidrome_playlist.service_id)
existing_track_ids = {track.service_id for track in existing_tracks}
new_tracks = [track for track in matched_tracks if track.service_id not in existing_track_ids]

# Add only new tracks to Navidrome
if new_tracks:
    navidrome.add_tracks_to_playlist(
        playlist_id=navidrome_playlist.service_id,
        track_ids=[track.service_id for track in new_tracks],
    )

# Done! Your Spotify playlist has been copied to Navidrome
# You can modify this script to work in reverse, so it
# copies from Navidrome to Spotify if that's what you need.