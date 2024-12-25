# Navify

A Python script to mirror your Spotify playlists to Navidrome!
(support for other services is in progress)

---

# Usage

## Proof of Concept script

> [!IMPORTANT]  
> This was the original script. It is not actively maintained. A proper replacement can be found in the `examples` directory.

0. Create a Spotify app and set http://localhost:8888/callback as a callback url
1. Create a Python 3.10+ virtual environment and install requirements.txt, then enter the environment
2. Duplicate `.env.example`, then rename the duplicate to `.env` and set the values in it
3. run `navify.py` (e.g. `python3 navify.py`)

Alternatively use the `navify` PyPI package and build your own app or scripts.

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
|`DEEZER_ARL`|Optional|`None`|ARL token to authenticate with your Deezer account|

# Supported services
|Name|Write operations|Read operations|
|--|--|--|
|Spotify|Fully supported|Fully supported|
|Deezer|None supported|Fully supported|
|Subsonic (e.g. Navidrome)|Fully supported|Fully supported|

**Explanation:** Not all features are supported for each service. This largely depends on the third-party libraries being used to interface with streaming services. The primary goal for every service is to at least support read operations (e.g. able to fetch playlists but unable to create or update them).

# FAQ

### Is there a way to use Navify from the CLI?
Not at the moment. I'll look into it in the future because I see how it could be useful.
It isn't really a priority at the moment, but feel free to make one or contribute to this repository.

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