# tunesynctool

A Python package, CLI* and self-hostable service* to transfer and sync music between your local/commercial streaming services.

*Under development

Tunesynctool supports the following services:
- Spotify
- Deezer (read only, authentication is not currently supported, thus only public playlists can be accessed in read only mode)
- Any Subsonic-like service (Navidrome, Airsonic, etc.)
- YouTube Music

Support for other services is planned, however the current focus is on getting the self-hostable service to a stable state.

## Usage

Currently, the recommended way is to either use the Python package for custom scripts or use the included CLI commands.
Install the latest release vie PyPI (`pip install tunesynctool`).

## Configuration

Configuration options can be loaded from the environment or be manually specified in code. [Check here](https://github.com/WilliamNT/tunesynctool/wiki/Configuration) for more information.

# FAQ

## Why aren't there any updates to the CLI or Python package, even though the repository is active?
I decided that I'd prefer to develop a self-hostable application instead for various reasons that I detailed in a wiki article.

## Does tunesynctool offer functionality to download or stream music?
**No**, use the official clients' offline listening features for that, or source your music in other ways you prefer ;)

## How does matching work?

Learn more about matching [here](https://github.com/WilliamNT/tunesynctool/wiki/Track-matching).

## When will the self-hostable app be released?
I can't tell you that unfortunately. I am working on this project in my free time and due to studies and personal matters I have to pause development often.
Thank you for your patience and understanding.
