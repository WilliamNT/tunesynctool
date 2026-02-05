from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio

from api.routes.router import endpoints
from api.core.config import config
from api.core.database import initialize_database
from api.core.logging import logger
from api.workers.dispatcher import worker_dispatcher
from api.workers.recovery import recover_stale_tasks

app = FastAPI(
    title="tunesynctool web API",
    openapi_url=f"{config.API_BASE_URL}/openapi.json",
    description="Web API wrapper for the tunesynctool Python package with some extra features.",
)

worker_tasks: list[asyncio.Task] = []


@app.on_event("startup")
async def on_startup():
    logger.info("Starting application...")
    
    await initialize_database()
    
    recovered = await recover_stale_tasks()
    if recovered > 0:
        logger.info(f"Recovered {recovered} stale task(s) from previous run")
    
    worker_count = 3
    logger.info(f"Starting {worker_count} background workers...")
    for i in range(worker_count):
        task = asyncio.create_task(worker_dispatcher(i))
        worker_tasks.append(task)
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down application...")
    
    for task in worker_tasks:
        task.cancel()
        
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    
    logger.info("Application shutdown complete")


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