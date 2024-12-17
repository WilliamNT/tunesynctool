# Navify

A Python script to mirror your Spotify playlists to Navidrome!

---

# Warning!

This script and package are currently experimental. Contributions and testing with your own library are welcome.

---

# Usage

## Proof of Concept script
0. Create a Spotify app and set http://localhost:8888/callback as a callback url
1. Create a Python 3.10+ virtual environment and install requirements.txt, then enter the environment
2. Duplicate `.env.example`, then rename the duplicate to `.env` and set the values in it
3. run `navify.py` (e.g. `python3 navify.py`)

Alternatively use the `navify` package and build your own app or scripts.

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
|`PREVIEW_ONLY`|Optional|`true`|Wether to run in preview mode or not (allows you to validate matching without modifying your Subsonic library)|
|`WHITELISTED_PLAYLIST_IDS`|Optional|`None`|String consisting of comma seperated Spotify playlist ids, if set only these playlists will be mirrored (otherwise all will be)|

# FAQ

### Does this tool automatically syncronize future changes between services?
Not at the moment, but this will be supported in the future.

### Why is the tool so slow (even with small playlists)?
This is being worked on, the focus for the initial proof of concept was on matching accuracy.
Edit: The `navify` package is more optimized.

### Does this tool download missing songs?
No, but support for integrations with tools that can do this is planned.

### Can I export a list of missing songs?
Not at the moment, but this will be supported in the near future.

### How accurate is matching?
Based on my testing, it seems to be pretty accurate. If you face any accuracy issues, check this FAQ again and feel free to open an issue.

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
The tool attempts to guess correct ways to search and pull songs from your Subsonic service, then performs various matching strategies to check if the song from the streaming service and the results from the Subsonic API match. It does this by fuzzy string comparison, metadata normalization and some basic weighting.

### Do you plan to support streaming services other than Spotify?
Yes! The package was written in a way where you only have to develop a driver to interact with each streaming service and map the metadata to an internal data model. Once that's done, the matching logic is basically universal.

### What services are compatible?
Currently only Spotify and any other Subsonic compatible API.

### Why is there a seperate PyPI package with the same name along the script?
The navify.py script file served as a proof of concept rather than a finished product. The package is better structured and allows anyone to build custom scripts that fit their own needs. For those who don't want to, check out the `examples/` folder for ready to use scripts.

### How can I install the PyPI package?
1. Run `pip install navify` or add `navify` to your requirements.txt file in a new line.
2. After that, just import Navify like any other package: `from navify import x, y, z`
# To do

- ~~Simplify/refactor script, because it's a mess currently~~
- Proper documentation
- Maybe support other services like YouTube Music
- Add support for syncronization after the playlist has been mirrored (aka. sync changes from spotify)
    - Dockerize it and use a cron job to auto update from time to time
- ~~Performance improvements~~