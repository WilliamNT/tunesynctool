from fastapi import Request

from api.models.service import ProviderAboutRead, ProviderRead
from api.models.collection import Collection

class ProviderService:
    def get_supported_providers(self, request: Request) -> Collection[ProviderRead]:
        """
        Returns a collection of supported providers.
        
        :return: A collection of supported providers.
        """

        spotify = ProviderRead(
            provider_name="spotify",
            is_configured=True,
            ui=ProviderAboutRead(
                description="Connect your Spotify account to access Spotify specific features.",
                display_name="Spotify",
                favicon=str(request.url_for("static", path="providers/spotify_128.png"))
            )
        )

        youtube = ProviderRead(
            provider_name="youtube",
            is_configured=True,
            ui=ProviderAboutRead(
                description="Connect your Google account to access YouTube specific features.",
                display_name="YouTube",
                favicon=str(request.url_for("static", path="providers/youtube_128.png"))
            )
        )

        deezer = ProviderRead(
            provider_name="deezer",
            is_configured=True,
            ui=ProviderAboutRead(
                description="Set your Deezer ARL cookie to access Deezer specific features.",
                display_name="Deezer",
                favicon=str(request.url_for("static", path="providers/deezer_128.png"))
            )
        )

        subsonic = ProviderRead(
            provider_name="subsonic",
            is_configured=True,
            ui=ProviderAboutRead(
                description="A standardized API for media streaming services. Supports any Subsonic compatible service (e.g. Subsonic, Airsonic, Navidrome).",
                display_name="Subsonic and similar",
                favicon=str(request.url_for("static", path="providers/subsonic_128.png"))
            )
        )
        
        # This is a placeholder implementation. Replace with actual logic to retrieve supported providers.
        return Collection[ProviderRead](
            items=[
                spotify,
                youtube,
                deezer,
                subsonic
            ]
        )
    
def get_provider_service() -> ProviderService:
    return ProviderService()