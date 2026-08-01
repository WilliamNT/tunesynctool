from typing import Optional
from redis.asyncio import Redis
import asyncio
import time

from api.models.task import TaskResponseBase, TaskStatus, PlaylistTaskStatus
from api.workers.utils.constants import TTL_FINISHED, TTL_RUNNING
from api.core.logging import logger

_DORMANT_TASK_STATUSES = [TaskStatus.CANCELED, TaskStatus.FAILED, TaskStatus.FINISHED, TaskStatus.MARKED_FOR_DELETION]

async def save_task(
    redis: Redis,
    task: TaskResponseBase,
    redis_key: str,
    status: Optional[TaskStatus] = None,
    status_reason: Optional[str] = None,
    use_finished_ttl: bool = True
) -> bool:
    """
    Update a task in Redis, optionally setting a new status, unless it has gone dormant.

    :param redis: Redis client
    :param task: Task object to update
    :param redis_key: Full Redis key (user_tasks:{kind}:{user_id}:{task_id})
    :param status: New status, or None to keep the current one
    :param status_reason: Optional reason message
    :param use_finished_ttl: If True, use TTL_FINISHED; otherwise TTL_RUNNING
    :return: True if written, False if the task was dormant or gone
    """

    old_status = task.status

    if status is not None:
        task.status = status
        task.status_reason = status_reason
        if status in (TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.CANCELED):
            task.done_at = int(time.time())

    current = await redis.get(redis_key)
    if current is None:
        return False

    current_status = PlaylistTaskStatus.model_validate_json(current).status
    if current_status in _DORMANT_TASK_STATUSES:
        if current_status == TaskStatus.MARKED_FOR_DELETION:
            await redis.delete(redis_key)
        return False

    ttl = TTL_FINISHED if use_finished_ttl else TTL_RUNNING
    await redis.set(name=redis_key, value=task.model_dump_json(), ex=ttl)
    logger.debug(f"[task:{task.task_id}] Status: {old_status} -> {task.status}")
    return True

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

    await save_task(
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

    await save_task(
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

    await save_task(
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

    await save_task(
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

    await save_task(
        redis=redis,
        task=task,
        redis_key=redis_key,
        status=TaskStatus.RUNNING,
        status_reason=None,
        use_finished_ttl=False
    )

async def check_if_task_is_dormant(redis: Redis, redis_key: str) -> bool:
    """
    Check if a task is dormant for whatever reason.

    A task marked for deletion is removed here. Other dormant tasks are left in history.

    :param redis: Redis client
    :param redis_key: Full Redis key
    :return: True if task is dormant or no longer exists
    """

    raw = await redis.get(redis_key)

    if raw is None:
        logger.debug(f"Task key {redis_key} no longer exists")
        return True

    task = PlaylistTaskStatus.model_validate_json(raw)

    if task.status == TaskStatus.MARKED_FOR_DELETION:
        await redis.delete(redis_key)
        return True

    return task.status in _DORMANT_TASK_STATUSES

async def sleep_unless_dormant(redis: Redis, redis_key: str, seconds: int) -> bool:
    """
    Sleep for up to `seconds`, waking early if the task goes dormant.

    :param redis: Redis client
    :param redis_key: Full Redis key
    :param seconds: Maximum time to sleep
    :return: True if the task went dormant, False if the full duration elapsed
    """

    try:
        await asyncio.wait_for(_wait_until_dormant(redis, redis_key), timeout=seconds)
        return True
    except asyncio.TimeoutError:
        return False

async def _wait_until_dormant(redis: Redis, redis_key: str) -> None:
    while not await check_if_task_is_dormant(redis, redis_key):
        await asyncio.sleep(1)