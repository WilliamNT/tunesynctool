from fastapi import APIRouter

from .spotify import router as spotify_router
from .deezer import router as deezer_router
from .subsonic import router as subsonic_router
from .youtube import router as youtube_router

router = APIRouter(
    prefix="/providers",
)

router.include_router(spotify_router)
router.include_router(deezer_router)
router.include_router(subsonic_router)
router.include_router(youtube_router)