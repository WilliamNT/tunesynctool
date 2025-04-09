from fastapi import APIRouter

from .users import router as users_router
from .auth import router as auth_router
from .providers import endpoints as providers_endpoints

endpoints = APIRouter()

endpoints.include_router(users_router)
endpoints.include_router(auth_router)
endpoints.include_router(providers_endpoints)