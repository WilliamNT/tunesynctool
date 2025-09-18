from typing import Annotated
from fastapi import Depends, Request

from api.models.service import ProviderAboutRead, ProviderRead, ProviderLinkingRead, ProviderLinkType
from api.models.collection import Collection
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.services.auth_service import AuthService, get_auth_service
from api.core.config import config

class ProviderService:
    def __init__(self, credentials_service: CredentialsService, auth_service: AuthService) -> None:
        self.credentials_service = credentials_service
        self.auth_service = auth_service

    async def get_supported_providers(self, request: Request, jwt: str) -> Collection[ProviderRead]:
        """
        Returns a collection of supported providers.
        
        :param request: The request object.
        :param jwt: The JWT token for authentication.
        :return: A collection of supported providers.
        """

        user = await self.auth_service.resolve_user_from_jwt(jwt)

        spotify = ProviderRead(
            provider_name="spotify",
            is_configured=not config.DISABLE_SPOTIFY_PROVIDER,
            linking=ProviderLinkingRead(
                link_type=ProviderLinkType.OAUTH2,
                target_url=str(request.url_for("spotify:authorize")),
                linked=await self.credentials_service.is_linked(
                    user=user,
                    service_name="spotify"
                )
            ),
            ui=ProviderAboutRead(
                description="Connect your Spotify account to access Spotify specific features.",
                display_name="Spotify",
                favicon=str(request.url_for("static", path="providers/spotify_128.png"))
            )
        )

        youtube = ProviderRead(
            provider_name="youtube",
            is_configured=not config.DISABLE_GOOGLE_PROVIDER,
            linking=ProviderLinkingRead(
                link_type=ProviderLinkType.OAUTH2,
                target_url=str(request.url_for("youtube:authorize")),
                linked=await self.credentials_service.is_linked(
                    user=user,
                    service_name="youtube"
                )
            ),
            ui=ProviderAboutRead(
                description="Connect your Google account to access YouTube specific features.",
                display_name="YouTube",
                favicon=str(request.url_for("static", path="providers/youtube_128.png"))
            )
        )

        deezer = ProviderRead(
            provider_name="deezer",
            is_configured=True,
            linking=ProviderLinkingRead(
                link_type=ProviderLinkType.FORM,
                target_url=str(request.url_for("deezer:set_deezer_arl")),
                linked=await self.credentials_service.is_linked(
                    user=user,
                    service_name="deezer"
                )
            ),
            ui=ProviderAboutRead(
                description="Set your Deezer ARL cookie to access Deezer specific features.",
                display_name="Deezer",
                favicon=str(request.url_for("static", path="providers/deezer_128.png"))
            )
        )

        subsonic = ProviderRead(
            provider_name="subsonic",
            is_configured=not config.DISABLE_SUBSONIC_PROVIDER,
            linking=ProviderLinkingRead(
                link_type=ProviderLinkType.FORM,
                target_url=str(request.url_for("subsonic:set_subsonic_credentials")),
                linked=await self.credentials_service.is_linked(
                    user=user,
                    service_name="subsonic"
                )
            ),
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
    
def get_provider_service(credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)], auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> ProviderService:
    return ProviderService(
        credentials_service=credentials_service,
        auth_service=auth_service
    )