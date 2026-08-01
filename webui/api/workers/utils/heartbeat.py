import time
import asyncio

from api.workers.utils.context import WorkerContext
from api.workers.utils.constants import HEARTBEAT_INTERVAL
from api.workers.utils.task_status import save_task
from api.core.logging import logger

async def update_heartbeat(ctx: WorkerContext) -> None:
    """
    Update task heartbeat timestamp.
    """

    if not ctx.current_task or not ctx.current_redis_key:
        return
    
    ctx.current_task.last_heartbeat = int(time.time())
    ctx.current_task.worker_id = ctx.worker_name
    await save_task(ctx.redis, ctx.current_task, ctx.current_redis_key, use_finished_ttl=False)

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