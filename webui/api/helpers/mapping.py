from tunesynctool.models import Track

from api.models.track import TrackRead, TrackIdentifiersRead
from api.models.entity import EntityMetaRead, EntityMultiAuthorRead, EntityAssetsBase
from api.models.service import ServiceCredentials
from api.helpers.extraction import extract_deezer_cover, extract_spotify_cover, extract_youtube_cover

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