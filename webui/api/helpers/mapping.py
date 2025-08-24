from tunesynctool.models import Track
from tunesynctool.models.playlist import Playlist
import re

from api.models.track import TrackRead, TrackIdentifiersRead
from api.models.entity import EntityIdentifiersBase, EntityMetaRead, EntityMultiAuthorRead, EntityAssetsBase, EntitySingleAuthorRead
from api.helpers.extraction import extract_share_url_from_track_sync
from api.core.logging import logger
from api.models.playlist import PlaylistRead

def map_track_between_domain_model_and_response_model(
    track: Track,
    provider_name: str,
    assets: EntityAssetsBase
) -> TrackRead:
    meta = map_track_meta_from_domain_model_to_response_model(
        track=track,
        provider_name=provider_name
    )
        
    artists = EntityMultiAuthorRead(
        primary=track.primary_artist,
        collaborating=track.additional_artists
    )

    identifiers = TrackIdentifiersRead(
        provider_id=str(track.service_id),
        musicbrainz=track.musicbrainz_id,
        isrc=track.isrc
    )

    mapped = TrackRead(
        title=track.title,
        album_name=track.album_name,
        duration=track.duration_seconds,
        track_number=track.track_number,
        release_year=track.release_year,
        author=artists,
        meta=meta,
        identifiers=identifiers,
        assets=assets
    )

    return mapped

def map_playlist_meta_from_domain_model_to_response_model(playlist: Playlist, provider_name: str) -> EntityMetaRead:
    share_url = None

    extra_data = playlist.service_data

    if playlist.service_data:
        match provider_name:
            case "spotify":
                share_url = extra_data.get("external_urls", {}).get("spotify")
            case "youtube":
                share_url = f"https://music.youtube.com/playlist?list={playlist.service_id}" # api response does not contain a cononical URL
            case "deezer":
                share_url = f"https://www.deezer.com/playlist/{playlist.service_id}"
            case "subsonic":
                # Not applicable for this case because the Subsonic standard does not offer this feature
                # however I want to leave this note for clarification
                share_url = None

    return EntityMetaRead(
        provider_name=provider_name,
        share_url=share_url
    )

def map_track_meta_from_domain_model_to_response_model(track: Track, provider_name: str) -> EntityMetaRead:
    share_url = None
    extra_data = track.service_data
    
    sync_extractables = ["spotify", "youtube"]
    if track.service_name in sync_extractables:
        share_url = extract_share_url_from_track_sync(partial_data=extra_data, provider_name=provider_name)
    else:
        logger.debug(f"We either don't have an implementation for \"{provider_name}\" or it doesn't support it.")
    return EntityMetaRead(
        provider_name=provider_name,
        share_url=share_url
    )

def map_playlist_assets_between_domain_model_to_response_model(playlist: Playlist) -> EntityAssetsBase:
    link = None
    extra_data = playlist.service_data

    match playlist.service_name:
        case "spotify":
            link = extra_data.get("images", [])[0].get("url") if extra_data.get("images") and len(extra_data.get("images")) > 0 else None
        case "youtube":
            link = extra_data.get("thumbnails", {})[0].get("url") if extra_data.get("thumbnails") and len(extra_data.get("thumbnails")) > 0 else None
            pattern = re.compile(r'^(?:https?://)?(?:www\.)?gstatic\.com/youtube/media/ytm/images/pbg/playlist-empty-state-@\d+\.[a-z]+$', re.IGNORECASE)
            if link and bool(pattern.match(link)):
                link = None
        case "deezer", "subsonic":
            # TODO: add support for Deezer and Subsonic playlist cover art
            pass

    return EntityAssetsBase(
           cover_image=link
       )

def map_playlist_between_domain_model_to_response_model(playlist: Playlist, provider_name: str) -> PlaylistRead:
    meta = map_playlist_meta_from_domain_model_to_response_model(
        playlist=playlist,
        provider_name=provider_name
    )

    author = EntitySingleAuthorRead(
        primary=playlist.author_name
    )

    identifiers = EntityIdentifiersBase(
        provider_id=str(playlist.service_id)
    )

    assets = map_playlist_assets_between_domain_model_to_response_model(
        playlist=playlist
    )

    return PlaylistRead(
        title=playlist.name,
        description=playlist.description,
        is_public=playlist.is_public,
        author=author,
        meta=meta,
        identifiers=identifiers,
        assets=assets
    )