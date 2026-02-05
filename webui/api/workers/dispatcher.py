from redis.asyncio import Redis
import asyncio
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from api.core.logging import logger
from api.core.config import config
from api.models.task import PlaylistTaskStatus, TaskStatus, TaskKind
from api.models.user import User
from api.workers.handlers.playlist_transfer_handler import handle_playlist_transfer
from api.workers.handlers.helpers import report_task_on_hold, report_task_failure
from api.services.user_service import UserService
from api.core.database import get_session
from api.workers.keys import (
    parse_task_key, 
    make_task_queue_name, 
    TTL_RUNNING, 
    HEARTBEAT_INTERVAL
)

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

async def update_heartbeat(ctx: WorkerContext) -> None:
    """
    Update task heartbeat timestamp.
    """

    if not ctx.current_task or not ctx.current_redis_key:
        return
    
    ctx.current_task.last_heartbeat = int(time.time())
    ctx.current_task.worker_id = ctx.worker_name
    await ctx.redis.set(ctx.current_redis_key, ctx.current_task.model_dump_json(), ex=TTL_RUNNING)

async def start_heartbeat_loop(ctx: WorkerContext) -> None:
    """
    Background task to update heartbeat while processing.
    """
    
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        await update_heartbeat(ctx)
        logger.debug(f"[{ctx.worker_name}] Heartbeat updated for task {ctx.current_task.task_id}")

async def stop_heartbeat(ctx: WorkerContext) -> None:
    """
    Stop the heartbeat background task if running.
    """

    if ctx.heartbeat_task:
        ctx.heartbeat_task.cancel()
        try:
            await ctx.heartbeat_task
        except asyncio.CancelledError:
            pass
        ctx.heartbeat_task = None

async def fetch_next_task(ctx: WorkerContext) -> Optional[Tuple[str, str, int, str]]:
    """
    Wait for and fetch the next task from the queue.
    
    :return: Tuple of (redis_key, task_kind, user_id, task_uuid) or None if no task available
    """

    next_in_queue = await ctx.redis.blpop(make_task_queue_name(), timeout=5)
    if not next_in_queue:
        return None

    redis_key = next_in_queue[1]

    try:
        task_kind, user_id, task_uuid = parse_task_key(redis_key)
    except ValueError as e:
        logger.error(f"[{ctx.worker_name}] Invalid task key format: {redis_key}. Error: {e}")
        return None

    return redis_key, task_kind, user_id, task_uuid

async def load_and_validate_task(ctx: WorkerContext, redis_key: str, task_uuid: str) -> Optional[PlaylistTaskStatus]:
    """
    Load task from Redis and validate its status.
    
    :return: The task if valid, None otherwise
    """

    unparsed_task = await ctx.redis.get(redis_key)
    if not unparsed_task:
        logger.warning(f"[{ctx.worker_name}][task:{task_uuid}] Task data not found in Redis (may have expired or been cancelled)")
        return None

    task = PlaylistTaskStatus.model_validate_json(unparsed_task)

    if task.status == TaskStatus.CANCELED:
        logger.info(f"[{ctx.worker_name}][task:{task_uuid}] Task was cancelled before pickup, skipping")
        return None
    
    if task.status != TaskStatus.QUEUED:
        logger.warning(f"[{ctx.worker_name}][task:{task_uuid}] Task status is {task.status}, expected QUEUED. Skipping.")
        return None

    return task

async def mark_task_running(ctx: WorkerContext, task: PlaylistTaskStatus, redis_key: str, task_uuid: str) -> None:
    """
    Mark a task as running and set initial heartbeat.
    """

    task.status = TaskStatus.RUNNING
    task.started_at = int(time.time())
    task.worker_id = ctx.worker_name
    task.last_heartbeat = int(time.time())
    await ctx.redis.set(redis_key, task.model_dump_json(), ex=TTL_RUNNING)
    
    logger.info(f"[{ctx.worker_name}][task:{task_uuid}] Status: QUEUED -> RUNNING")

async def get_task_user(ctx: WorkerContext, user_id: int, task_uuid: str) -> Optional[User]:
    """
    Fetch the user who owns the task.
    """

    session = await anext(get_session())
    try:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id)

        if not user:
            logger.error(f"[{ctx.worker_name}][task:{task_uuid}] User {user_id} not found")
        
        return user
    finally:
        await session.close()

async def dispatch_task(ctx: WorkerContext, task_kind: str, task: PlaylistTaskStatus, user: User, redis_key: str) -> None:
    """
    Dispatch task to the appropriate handler based on task kind.
    """

    match task_kind:
        case TaskKind.USER_INITIATED_PLAYLIST_TRANSFER:
            await handle_playlist_transfer(
                task=task, 
                user=user, 
                redis=ctx.redis,
                redis_key=redis_key
            )
        case _:
            logger.error(f"[{ctx.worker_name}][task:{task.task_id}] Unrecognized task type: {task_kind}")
            await report_task_failure(ctx.redis, task, redis_key, f"Unknown task type: {task_kind}")

async def process_single_task(ctx: WorkerContext) -> bool:
    """ 
    Process a single task from the queue.
    
    :return: True if a task was processed, False if queue was empty
    """

    result = await fetch_next_task(ctx)
    if not result:
        return False

    redis_key, task_kind, user_id, task_uuid = result
    ctx.current_redis_key = redis_key

    logger.info(f"[{ctx.worker_name}][task:{task_uuid}] Picked up task from queue")

    task = await load_and_validate_task(ctx, redis_key, task_uuid)
    if not task:
        ctx.current_redis_key = None
        return True

    ctx.current_task = task
    await mark_task_running(ctx, task, redis_key, task_uuid)

    ctx.heartbeat_task = asyncio.create_task(start_heartbeat_loop(ctx))

    try:
        user = await get_task_user(ctx, user_id, task_uuid)
        if not user:
            await report_task_failure(ctx.redis, task, redis_key, "User not found.")
            return True

        await dispatch_task(ctx, task_kind, task, user, redis_key)
    finally:
        await stop_heartbeat(ctx)
        ctx.current_task = None
        ctx.current_redis_key = None

    return True

async def handle_shutdown(ctx: WorkerContext) -> None:
    """
    Handle graceful shutdown of the worker.
    """

    logger.info(f"[{ctx.worker_name}] Received shutdown signal")
    
    await stop_heartbeat(ctx)
    
    if ctx.current_task and ctx.current_redis_key:
        logger.info(f"[{ctx.worker_name}][task:{ctx.current_task.task_id}] Marking task as ON_HOLD due to shutdown")
        await report_task_on_hold(
            redis=ctx.redis,
            task=ctx.current_task,
            redis_key=ctx.current_redis_key,
            reason="Worker shutdown. Task will be retried."
        )
    
    await ctx.redis.aclose()
    logger.info(f"[{ctx.worker_name}] Shutdown complete")

async def handle_error(ctx: WorkerContext, error: Exception) -> None:
    """
    Handle unexpected errors in the worker.
    """

    logger.error(f"[{ctx.worker_name}] Unexpected error: {error}", exc_info=True)
    
    if ctx.current_task and ctx.current_redis_key:
        try:
            await report_task_failure(ctx.redis, ctx.current_task, ctx.current_redis_key, f"Worker error: {error}")
        except Exception:
            pass
    
    await ctx.redis.aclose()

async def worker_dispatcher(worker_id: int) -> None:
    """
    Main worker loop that processes tasks from the Redis queue.
    
    :param worker_id: Unique identifier for this worker instance
    """

    ctx = WorkerContext(
        worker_id=worker_id,
        worker_name=f"worker-{worker_id}",
        redis=Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True
        )
    )

    logger.info(f"[{ctx.worker_name}] Starting up...")

    try:
        while True:
            task_processed = await process_single_task(ctx)
            if task_processed:
                await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        await handle_shutdown(ctx)
        raise
    except Exception as e:
        await handle_error(ctx, e)
        raise