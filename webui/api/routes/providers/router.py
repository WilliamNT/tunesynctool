from fastapi import APIRouter

from .spotify import router as spotify_router
from .deezer import router as deezer_router
from .subsonic import router as subsonic_router

endpoints = APIRouter(
    prefix="/providers",
)

endpoints.include_router(spotify_router)
endpoints.include_router(deezer_router)
endpoints.include_router(subsonic_router)