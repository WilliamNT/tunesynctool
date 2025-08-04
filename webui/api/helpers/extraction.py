from typing import Optional, List

def _raise_if_invalid_provider(valid_names: List[str], provider_name: str):
    if not provider_name in valid_names:
        valid_names = ", ".join(valid_names)
        raise ValueError(f"Invalid provider name for an extractor was passed. You passed \"{provider_name}\" which is not recognized. Valid options are: {valid_names}.")

def extract_spotify_cover(data: dict) -> Optional[str]:
    return data.get("album", {}).get("images", [{}])[0].get("url")

def extract_youtube_cover(data: dict) -> Optional[str]:
    return data.get("track", {}).get("videoDetails", {}).get("thumbnail", {}).get("thumbnails", [{}])[0].get("url")

def extract_deezer_cover(data: dict) -> Optional[str]:
    return data.get("album", {}).get("cover")

_SYNC_TRACK_ASSET_EXTRACTORS = {
    "spotify": extract_spotify_cover,
    "youtube": extract_youtube_cover,
    "deezer": extract_deezer_cover
}

def extract_cover_link_for_track_sync(partial_data: dict, provider_name: str) -> Optional[str]:
    _raise_if_invalid_provider(
        valid_names=_SYNC_TRACK_ASSET_EXTRACTORS.keys(),
        provider_name=provider_name
    )
    
    return _SYNC_TRACK_ASSET_EXTRACTORS[provider_name](
        data=partial_data
    )

def extract_spotify_share_url(data: dict) -> Optional[str]:
    url = data.get("external_urls", {}).get("spotify")

    _id = data.get("id")
    if not url and _id:
        url = f"https://open.spotify.com/playlist/{_id}"

    return url

def extract_youtube_share_url(data: dict) -> Optional[str]:
    url = data.get("track", {}).get("microformat", {}).get("microformatDataRenderer", {}).get("urlCanonical")
    
    _id = data.get("videoId")
    if not url and _id:
        url = f"https://music.youtube.com/watch?v={_id}"

    return url

_SYNC_TRACK_SHARE_URL_EXTRACTORS = {
    "spotify": extract_spotify_share_url,
    "youtube": extract_youtube_share_url,
}

def extract_share_url_from_track_sync(partial_data: dict, provider_name: str) -> Optional[str]:
    _raise_if_invalid_provider(
        valid_names=_SYNC_TRACK_SHARE_URL_EXTRACTORS.keys(),
        provider_name=provider_name
    )

    return _SYNC_TRACK_SHARE_URL_EXTRACTORS[provider_name](
        data=partial_data
    )