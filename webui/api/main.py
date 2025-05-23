from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.router import endpoints
from api.core.config import config
from api.core.database import initialize_database

app = FastAPI(
    title="tunesynctool web API",
    openapi_url=f"{config.API_BASE_URL}/openapi.json",
    description="Web API wrapper for the tunesynctool Python package with some extra features.",
)

@app.on_event("startup")
async def on_startup():
    await initialize_database()

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

app.mount(
    path="/static",
    app=StaticFiles(directory="static"),
    name="static",
)