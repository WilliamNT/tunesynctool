from fastapi import APIRouter

from .users import router as users_router
from .auth import router as auth_router
from .providers import router as providers_router
from .catalog import router as catalog_router
from .tasks import router as tasks_router
from .library import router as library_router

from .providers.spotify import router as spotify_router
from .providers.deezer import router as deezer_router
from .providers.subsonic import router as subsonic_router
from .providers.youtube import router as youtube_router

endpoints = APIRouter()

endpoints.include_router(users_router)
endpoints.include_router(auth_router)
endpoints.include_router(providers_router)
endpoints.include_router(catalog_router)
endpoints.include_router(tasks_router)
endpoints.include_router(library_router)
endpoints.include_router(spotify_router)
endpoints.include_router(deezer_router)
endpoints.include_router(subsonic_router)
endpoints.include_router(youtube_router)