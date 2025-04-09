from fastapi import APIRouter

from .users import router as users_router

endpoints = APIRouter()

endpoints.include_router(users_router)