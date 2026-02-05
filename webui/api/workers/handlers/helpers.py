from typing import Optional
from redis.asyncio import Redis
import time

from api.models.task import TaskResponseBase, TaskStatus, PlaylistTaskStatus
from api.workers.keys import TTL_FINISHED, TTL_RUNNING
from api.core.logging import logger

async def _end_task(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str, 
    status: TaskStatus, 
    status_reason: Optional[str] = None,
    use_finished_ttl: bool = True
) -> None:
    """
    Update task to a terminal or intermediate state.
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key (user_tasks:{kind}:{user_id}:{task_id})
    :param status: New status
    :param status_reason: Optional reason message
    :param use_finished_ttl: If True, use TTL_FINISHED; otherwise TTL_RUNNING
    """

    old_status = task.status
    task.status = status
    task.status_reason = status_reason
    
    ttl = TTL_FINISHED if use_finished_ttl else TTL_RUNNING
    
    if status in (TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELED):
        task.done_at = int(time.time())

    await redis.set(
        name=redis_key,
        value=task.model_dump_json(),
        ex=ttl
    )
    
    logger.debug(f"[task:{task.task_id}] Status: {old_status} -> {status}")

async def report_task_failure(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str, 
    reason: Optional[str] = "An error occurred."
) -> None:
    """
    Mark task as failed.
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key
    :param reason: Optional reason message
    """

    logger.warning(f"[task:{task.task_id}] Task failed: {reason}")

    await _end_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.FAILED,
        status_reason=reason
    )

async def report_task_cancellation(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str, 
    reason: Optional[str] = "Task was cancelled."
) -> None:
    """
    Mark task as cancelled.
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key
    :param reason: Optional reason message
    """

    logger.info(f"[task:{task.task_id}] Task cancelled: {reason}")

    await _end_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.CANCELED,
        status_reason=reason
    )

async def report_task_on_hold(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str, 
    reason: Optional[str] = "Paused. Will resume automatically."
) -> None:
    """
    Mark task as on hold (temporary pause).
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key
    :param reason: Optional reason message
    """

    await _end_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.ON_HOLD,
        status_reason=reason,
        use_finished_ttl=False  # On hold tasks should resume, use running TTL
    )

async def report_task_finished(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str
) -> None:
    """
    Mark task as successfully completed.
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key
    """

    duration = ""

    if task.started_at:
        elapsed = int(time.time()) - task.started_at
        duration = f" (took {elapsed}s)"
    
    logger.info(f"[task:{task.task_id}] Task completed successfully{duration}")

    await _end_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.FINISHED,
        status_reason=None
    )

async def report_task_as_running(
    redis: Redis, 
    task: TaskResponseBase, 
    redis_key: str
) -> None:
    """
    Update task to running status (refreshes TTL).
    
    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key
    """

    await _end_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.RUNNING,
        status_reason=None,
        use_finished_ttl=False
    )

async def check_if_task_cancelled(redis: Redis, redis_key: str) -> bool:
    """
    Check if a task has been cancelled by the user.
    
    :param redis: Redis client
    :param redis_key: Full Redis key
    :return: True if task was cancelled or no longer exists
    """

    raw = await redis.get(redis_key)

    if raw is None:
        logger.debug(f"Task key {redis_key} no longer exists")
        return True
    
    task = PlaylistTaskStatus.model_validate_json(raw)
    return task.status == TaskStatus.CANCELED