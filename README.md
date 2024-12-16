# Navify

A Python script to mirror your Spotify playlists to Navidrome!

Why did I create this? I just really like the Spotify generated and other curated playlists and figured I'd sync them with my local library.

In theory this should work with any service based on the Subsonic API specification, but I only tested it with Navidrome.

---

# Usage

0. Create a Spotify app, set http://localhost:8888/callback as a callback url, the rest is self explanatory in the `.env.example`
1. Create a Python 3.10+ virtual environment and install requirements.txt, then enter the environment
2. Duplicate `.env.example`, rename the duplicate to `.env` and set the values in it
3. run `navify.py` (e.g. `python3 navify.py`)

# Warning!

This script is currently experimental. Contributions and testing with your own library are welcome.

# To do

- Simplify/refactor script, because it's a mess currently
- Proper documentation
- Maybe support other services like YouTube Music
- Would be cool if deemix or another alternative got integrated at some point
- Add support for syncronization after the playlist has been mirrored (aka. sync changes from spotify)
    - Dockerize it and use a cron job to auto update from time to 