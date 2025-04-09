from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from api.routes.router import endpoints
from api.core.config import config
from api.core.database import initialize_database

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title="tunescyntool web API",
    openapi_url=f"{config.API_BASE_URL}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    description="Web API wrapper for the tunescyntool Python package with some extra features.",
)

@app.on_event("startup")
def on_startup():
    initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router=endpoints,
    prefix=config.API_BASE_URL,
)