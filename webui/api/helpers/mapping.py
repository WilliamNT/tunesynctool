from tunesynctool.models import Track

from api.models.track import TrackRead, TrackIdentifiersRead
from api.models.entity import EntityMetaRead, EntityMultiAuthorRead, EntityAssetsBase
from tunesynctool.models.playlist import Playlist

def map_track_between_domain_model_and_response_model(
    track: Track,
    provider_name: str,
    assets: EntityAssetsBase
) -> TrackRead:
    meta = EntityMetaRead(
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