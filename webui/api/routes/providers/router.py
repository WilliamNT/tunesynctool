from fastapi import APIRouter

from .spotify import router as spotify_router

endpoints = APIRouter(
    prefix="/providers",
)

endpoints.include_router(spotify_router)