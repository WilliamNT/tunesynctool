from typing import Annotated
from fastapi import Depends
import random
import string
import hashlib

from api.services.providers.base_provider import BaseProvider
from api.services.credentials_service import CredentialsService, get_credentials_service
from api.core.config import config
from api.core.logging import logger
from api.models.entity import EntityAssetsBase

class SubsonicProvider(BaseProvider):
    def __init__(self, credentials_service):
        super().__init__(
            credentials_service=credentials_service,
            provider_name="subsonic"
        )

    async def get_track_assets(self, track, user): 
        if not track.service_data:
            return None

        cover_art = track.service_data.get("coverArt", None)
        if not cover_art:
            return None
        
        credentials = await self.get_credentials(user)
        
        password = credentials.credentials.get("password")
        if not password:
            logger.error(f"User {user.id} does not have a password for {self.provider_name} but still we fetched from the API successfully. This is likely a bug...")
            return None
        
        username = credentials.credentials.get("username")
        if not username:
            logger.error(f"User {user.id} does not have a username for {self.provider_name} but still we fetched from the API successfully. This is likely a bug...")
            return None

        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        token_input = password + salt
        token = hashlib.md5(token_input.encode('utf-8')).hexdigest()

        url = f"{config.SUBSONIC_BASE_URL}:{config.SUBSONIC_PORT}/rest/getCoverArt.view?id={cover_art}&s={salt}&t={token}&u={username}&v=1.8.0&c=tunesynctool&f=json"
        
        return EntityAssetsBase(
            cover_image=url
        )

def get_subsonic_provider(
    credentials_service: Annotated[CredentialsService, Depends(get_credentials_service)]
) -> SubsonicProvider:
    return SubsonicProvider(
        credentials_service=credentials_service
    )