from redis.asyncio import Redis
import time

from api.core.config import config
from api.core.logging import logger
from api.models.task import PlaylistTaskStatus, TaskStatus
from api.workers.keys import make_running_tasks_pattern, HEARTBEAT_STALE_THRESHOLD, TTL_FINISHED

async def recover_stale_tasks() -> int:
    """
    Scan for tasks stuck in RUNNING state with stale heartbeats.
    Mark them as FAILED so they don't appear stuck forever.
    
    :return: Number of stale tasks recovered
    """
    
    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True
    )
    
    recovered_count = 0
    current_time = int(time.time())
    
    try:
        async for key in redis.scan_iter(make_running_tasks_pattern()):
            raw = await redis.get(key)
            if not raw:
                continue
                
            try:
                task = PlaylistTaskStatus.model_validate_json(raw)
            except Exception:
                continue
            
            if task.status != TaskStatus.RUNNING:
                continue
            
            if task.last_heartbeat:
                age = current_time - task.last_heartbeat
                if age > HEARTBEAT_STALE_THRESHOLD:
                    logger.warning(
                        f"[task:{task.task_id}] Found stale task "
                        f"(last heartbeat {age}s ago, threshold {HEARTBEAT_STALE_THRESHOLD}s). "
                        f"Marking as FAILED."
                    )

                    task.status = TaskStatus.FAILED
                    task.status_reason = "Worker died unexpectedly. Task was not completed."
                    task.done_at = current_time

                    await redis.set(key, task.model_dump_json(), ex=TTL_FINISHED)

                    recovered_count += 1
            else:
                if task.started_at and (current_time - task.started_at) > HEARTBEAT_STALE_THRESHOLD:
                    logger.warning(
                        f"[task:{task.task_id}] Found stale task without heartbeat. "
                        f"Marking as FAILED."
                    )

                    task.status = TaskStatus.FAILED
                    task.status_reason = "Worker died unexpectedly. Task was not completed."
                    task.done_at = current_time

                    await redis.set(key, task.model_dump_json(), ex=TTL_FINISHED)

                    recovered_count += 1
    finally:
        await redis.aclose()
    
    return recovered_count
