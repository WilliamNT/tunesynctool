from dataclasses import dataclass
from typing import Optional
from redis.asyncio import Redis
import asyncio

from api.models.task import PlaylistTaskStatus

@dataclass
class WorkerContext:
    """
    Holds the current state of a worker.
    """

    worker_id: int
    worker_name: str
    redis: Redis
    current_task: Optional[PlaylistTaskStatus] = None
    current_redis_key: Optional[str] = None
    heartbeat_task: Optional[asyncio.Task] = None