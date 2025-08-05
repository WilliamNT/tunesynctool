from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio

from api.routes.router import endpoints
from api.core.config import config
from api.core.database import initialize_database
from api.workers.dispatcher import worker_dispatcher

app = FastAPI(
    title="tunesynctool web API",
    openapi_url=f"{config.API_BASE_URL}/openapi.json",
    description="Web API wrapper for the tunesynctool Python package with some extra features.",
)

worker_tasks: list[asyncio.Task] = []

@app.on_event("startup")
async def on_startup():
    await initialize_database()
    for i in range(3):

        task = asyncio.create_task(worker_dispatcher(i))
        worker_tasks.append(task)

@app.on_event("shutdown")
async def on_shutdown():
    for task in worker_tasks:
        task.cancel()
        
    await asyncio.gather(*worker_tasks, return_exceptions=True)

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