from typing import Optional
from redis.asyncio import Redis
import time

from api.models.task import TaskResponseBase, TaskStatus

async def _end_task(redis: Redis, task: TaskResponseBase, task_id: str, status: TaskStatus, status_reason: Optional[str] = None) -> None:
    task.status = status
    task.status_reason = status_reason
    task.done_at = int(time.time())

    await redis.set(
        name=task_id,
        value=task.model_dump_json()
    )

async def report_task_failure(redis: Redis, task: TaskResponseBase, task_id: str, reason: Optional[str] = "An error occured.") -> None:
    await _end_task(
        redis=redis,
        task=task,
        task_id=task_id,
        status=TaskStatus.FAILED,
        status_reason=reason
    )

async def report_task_cancellation(redis: Redis, task: TaskResponseBase, task_id: str, reason: Optional[str] = "Something went wrong.") -> None:
    await _end_task(
        redis=redis,
        task=task,
        task_id=task_id,
        status=TaskStatus.CANCELED,
        status_reason=reason
    )

async def report_task_on_hold(redis: Redis, task: TaskResponseBase, task_id: str, reason: Optional[str] = "Will be automatically resumed later.") -> None:
    await _end_task(
        redis=redis,
        task=task,
        task_id=task_id,
        status=TaskStatus.ON_HOLD,
        status_reason=reason
    )

async def report_task_finished(redis: Redis, task: TaskResponseBase, task_id: str) -> None:
    await _end_task(
        redis=redis,
        task=task,
        task_id=task_id,
        status=TaskStatus.FINISHED,
        status_reason=None
    )

async def report_task_as_running(redis: Redis, task: TaskResponseBase, task_id: str) -> None:
    await _end_task(
        redis=redis,
        task=task,
        task_id=task_id,
        status=TaskStatus.RUNNING,
        status_reason=None
    )