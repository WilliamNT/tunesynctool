import time
import asyncio

from api.workers.utils.context import WorkerContext
from api.workers.utils.constants import TTL_RUNNING, HEARTBEAT_INTERVAL
from api.core.logging import logger

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