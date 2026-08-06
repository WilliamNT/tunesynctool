# tunesynctool

A self-hostable service to transfer (and sync*) music between your local/commercial streaming services.

*work in progress, not yet available

Tunesynctool supports the following services:
- Spotify
- Deezer (read only, authentication is not currently supported, thus only public playlists can be accessed in read only mode)
- Any Subsonic-like service (Navidrome, Airsonic, etc.)
- YouTube Music

Support for other services is planned, however the current focus is on getting the self-hostable service to a stable state.

# How do I use this?

Depending on what you need, you can use one of the following links to learn more about this project.

- For the Web UI's API (OpenAPI schema can be also downloaded here): https://schema.tunesynctool.com/
- For the legacy CLI's command builder see: https://cli.tunesynctool.com/
- For the wiki see: https://github.com/WilliamNT/tunesynctool/wiki

## Do you have a Discord?
[Yes.](https://dc.tunesynctool.com)

## When will the self-hostable app be released?
Soon! I am working on critical parts of the project at the moment. Once those are ready and everything works together nicely, I'll release a 1.0. Thank you for your patience and understanding.

## Stability

The project is under heavy development and contains bugs. Use at your own discretion.

## Usage

Currently you have to install the Python dependencies within requirements.txt and you'll be able to run the backend.

## Configuration

Configuration options can be loaded from the environment or be manually specified in code. [Check here](https://github.com/WilliamNT/tunesynctool/wiki/Configuration) for more information.

# FAQ

## Why aren't there any updates to the CLI or Python package, even though the repository is active?
I decided that I'd prefer to develop a self-hostable application instead for various reasons that I detailed in a wiki article.

## Does tunesynctool offer functionality to download or stream music?
**No**, use the official clients' offline listening features for that, or source your music in other ways you prefer ;)

## How does matching work?

> [!NOTE]  
> This is currently being entirely rebuilt from scratch. Stay tuned!

Learn more about matching [here](https://github.com/WilliamNT/tunesynctool/wiki/Track-matching).