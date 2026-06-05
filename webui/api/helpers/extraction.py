from typing import Optional, List

def extract_best_youtube_thumbnail(thumbnails: dict | list | None) -> Optional[str]:
    if isinstance(thumbnails, dict):
        for key in ["maxres", "standard", "high", "medium", "default"]:
            url = thumbnails.get(key, {}).get("url")
            if url:
                return url

        for thumbnail in thumbnails.values():
            if isinstance(thumbnail, dict) and thumbnail.get("url"):
                return thumbnail.get("url")

    if isinstance(thumbnails, list):
        for thumbnail in reversed(thumbnails):
            if isinstance(thumbnail, dict) and thumbnail.get("url"):
                return thumbnail.get("url")

    return None

def _raise_if_invalid_provider(valid_names: List[str], provider_name: str):
    if not provider_name in valid_names:
        valid_names = ", ".join(valid_names)
        raise ValueError(f"Invalid provider name for an extractor was passed. You passed \"{provider_name}\" which is not recognized. Valid options are: {valid_names}.")

def extract_spotify_cover(data: dict) -> Optional[str]:
    return data.get("album", {}).get("images", [{}])[0].get("url")

def extract_youtube_cover(data: dict) -> Optional[str]:
    official_track_data = data.get("track", data)
    official_thumbnail = extract_best_youtube_thumbnail(
        official_track_data.get("snippet", {}).get("thumbnails")
    )

    if official_thumbnail:
        return official_thumbnail

    return extract_best_youtube_thumbnail(
        data.get("track", {}).get("videoDetails", {}).get("thumbnail", {}).get("thumbnails")
    )

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
    
    _id = (
        data.get("videoId")
        or data.get("id")
        or data.get("track", {}).get("id")
        or data.get("search", {}).get("id", {}).get("videoId")
    )
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
