# Navify

A Python packaget to transfer music between your local/commercial streaming services. Supports track matching.

---

# Usage

Firstly, install the latest release vie PyPI (`pip install navify`).

## Configuration

How to read the table below: if a value is marked as optional and the default value associated with it isn't `None`, the default value will be used as a fallback if the environmental variable isn't provided.

|Variable name|Is it required?|Default value|Description|
|--|--|--|--|
|`SPOTIFY_CLIENT_ID`|Required|`None`|Client ID of the Spotify app you created|
|`SPOTIFY_CLIENT_SECRET`|Required|`None`|Client secret of the Spotify app you created|
|`SPOTIFY_REDIRECT_URI`|Optional|`http://localhost:8888/callback`|Callback URL of the Spotify app you created (don't forget to add this in your app's settings!)
|`SUBSONIC_BASE_URL`|Optional|`http://127.0.0.1`|Base URL of your Subsonic compatible API|
|`SUBSONIC_PORT`|Optional|`4533`|Port of your Subsonic compatible API|
|`SUBSONIC_USERNAME`|Required|`None`|Username to authenticate with your Subsonic compatible service|
|`SUBSONIC_PASSWORD`|Required|`None`|Password to authenticate with your Subsonic compatible service|
|`WHITELISTED_PLAYLIST_IDS`|Optional|`None`|String consisting of comma seperated Spotify playlist ids, if set only these playlists will be mirrored (otherwise all will be)|
|`DEEZER_ARL`|Optional|`None`|ARL token to authenticate with your Deezer account|
|`YOUTUBE_REQUEST_HEADERS`|Optional|`None`|Raw request headers from an authenticated request sent by your browser to music.youtube.com|

# Supported services
|Name|Write operations|Read operations|
|--|--|--|
|Spotify|Fully supported|Fully supported|
|Deezer|None supported|Fully supported|
|Subsonic (e.g. Navidrome)|Fully supported|Fully supported|
|YouTube Music|Fully supported|Fully supported|

**Explanation:** Not all features are supported for each service. This largely depends on the third-party libraries being used to interface with streaming services. The primary goal for every service is to at least support read operations (e.g. able to fetch playlists but unable to create or update them).

### Services I want to support in the future
- Jellyfin
- Apple Music
- Tidal
- Amazon Music
- SoundCloud

There is no guarantee that I will actually be able to support these services. Even if a well tested package is available for a service, I like testing my implementations before
releasing a driver. Also I don't have unlimited money to sign up for all of them. If you have a subscription to one of these and would like to contribute to this project, I'll be very grateful.

# FAQ

### Is there a way to use Navify from the CLI?
Not at the moment. I'll look into it in the future because I see how it could be useful.
It isn't really a priority at the moment, but feel free to make one or contribute to this repository.

### Does this package offer functionality to download or stream music?
No, use the official clients for that.

### How accurate is matching?
Based on my testing, it seems to be pretty accurate. If you face any accuracy issues please open an issue so I can improve it.

### What is required for matching to work?
The tool works only with properly tagged songs. The following are taken into account when the tool looks for matches:
- Title
- Album name
- Primary (album) artist name
- Duration in seconds
- Track number
- ISRC code
- MusicBrainz ID
- Additional artists' names
- Release year

### How can I automatically tag my songs?
You can use [MusicBrainz Picard](https://picard.musicbrainz.org/) for that.

### How does matching work?
The tool attempts to guess correct ways to search and pull songs from your target service, then performs various matching strategies to check if the song from the streaming service and the results from the searches match. It does this by fuzzy string comparison, metadata normalization and some basic weighting.

### How can I install the PyPI package?
1. Run `pip install navify` or add `navify` to your requirements.txt file in a new line.
2. After that, just import Navify like any other package: `from navify import x, y, z`

# To do

- Proper documentation