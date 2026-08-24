from dataclasses import dataclass


@dataclass
class TargetStyle:
    name: str
    supports_direct_isrc_querying: bool = False
    supports_musicbrainz_id_querying: bool = False