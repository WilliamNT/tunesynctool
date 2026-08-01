from typing import AsyncGenerator, List, Optional
import uuid
from fastapi import HTTPException, status
from redis.asyncio import Redis
import time

from api.models.task import PlaylistTaskProgress, PlaylistTaskStatus, PlaylistTaskCreate, TaskStatus, TaskKind
from api.models.user import User
from api.core.redis import get_redis_instance
from api.models.collection import Collection
from api.core.logging import logger
from api.workers.utils.keys import make_task_key, make_user_tasks_pattern, make_task_queue_name, make_kind_agnostic_user_task_pattern
from api.workers.utils.constants import TTL_QUEUED, TTL_FINISHED, SCAN_COUNT
from api.models.system import Initiator

_ACTIVE_STATUSES = [TaskStatus.RUNNING, TaskStatus.QUEUED, TaskStatus.ON_HOLD]

class TaskService:    
    def __init__(self, redis: Redis):
        self.redis = redis
        
    async def dispatch_playlist_transfer(self, details: PlaylistTaskCreate, user: User) -> PlaylistTaskStatus:
        """
        Attempts to transfer the specified playlist from the source provider to the target provider.
        Replication is not guaranteed to be 100% successful.
        
        This starts a long running task. Clients can poll for the progress of the transfer.
        """

        task_id = str(uuid.uuid4())
        redis_key = make_task_key(details.kind, user.id, task_id)
        timestamp = int(time.time())

        job = PlaylistTaskStatus(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            arguments=details,
            progress=PlaylistTaskProgress(),
            queued_at=timestamp
        )

        await self.redis.set(
            name=redis_key,
            value=job.model_dump_json(),
            ex=TTL_QUEUED
        )

        await self.redis.rpush(make_task_queue_name(), redis_key)
        
        logger.info(f"[task:{task_id}] Created new playlist transfer task for user {user.id}")

        return job

    async def get_playlist_transfer_status(self, task_id: str, user: User) -> Optional[PlaylistTaskStatus]:
        """
        Get the status of a playlist transfer task.
        
        :param task_id: UUID of the task
        :param user: User who owns the task
            
        :return: PlaylistTaskStatus or None if not found
        """
        redis_key = make_task_key(TaskKind.USER_INITIATED_PLAYLIST_TRANSFER, user.id, task_id)
        task = await self.redis.get(redis_key)
        
        if task is None:
            return None

        return PlaylistTaskStatus.model_validate_json(task)

    async def get_all_tasks_for_user(self, user: User) -> List[PlaylistTaskStatus]:
        """
        Retrieves all tasks that belong to the given user, ignoring their kind, age or status.
        """

        tasks = []
        pattern = make_user_tasks_pattern(user.id)

        async for key in self.redis.scan_iter(pattern, count=SCAN_COUNT):
            raw = await self.redis.get(key)
        
            if raw:
                task = PlaylistTaskStatus.model_validate_json(raw)
                tasks.append(task)

        return tasks
    
    async def handle_compiling_tasks_for_user(self, user: User) -> Collection[PlaylistTaskStatus]:
        """
        Returns the return value of TaskService.get_all_tasks_for_user() wrapped in a Collection DTO.
        """

        return Collection(
            items=await self.get_all_tasks_for_user(user)
        )

    async def dispatch_task_cancellation(self, task_id: uuid.UUID, user: User) -> None:
        """
        Marks a task as cancelled. The worker will detect this and stop processing.

        Only active tasks are affected; terminal tasks are left untouched so they
        remain in the user's history. A non-existent task raises 404.

        :param task_id: UUID of the task
        :param user: User who owns the task
        """

        await self.cancel_task(
            task_id=task_id,
            user=user,
            initiator=Initiator.USER,
            reason="Cancelled by user."
        )

    async def cancel_task(self, task_id: uuid.UUID, user: User, initiator: Initiator, reason: Optional[str] = None) -> None:
        """
        Cancels a task if it is still active. Terminal tasks are kept in history.
        """

        keys = await self._resolve_task_keys(user.id, task_id, verb="cancel")

        for key in keys:
            task = await self._get_task(key)
            if task is None or task.status not in _ACTIVE_STATUSES:
                continue

            await self.update_task_status(
                key=key,
                new_status=TaskStatus.CANCELED,
                initiator=initiator,
                reason=reason
            )

    async def delete_task(self, task_id: uuid.UUID, user: User, initiator: Initiator, reason: Optional[str] = None) -> None:
        """
        Removes a task from the user's history.

        Terminal tasks are deleted from Redis immediately. Active tasks are marked
        MARKED_FOR_DELETION and are removed by the worker once it acknowledges the
        request. A non-existent task raises 404.
        """

        keys = await self._resolve_task_keys(user.id, task_id, verb="delete")

        if len(keys) > 1:
            logger.warning(f"[task:{task_id}] Multiple Redis keys matched for this task. All will be deleted.")

        for key in keys:
            task = await self._get_task(key)
            if task is None:
                continue

            if task.status in _ACTIVE_STATUSES:
                await self.update_task_status(
                    key=key,
                    new_status=TaskStatus.MARKED_FOR_DELETION,
                    initiator=initiator,
                    reason=reason,
                )
            else:
                await self.redis.delete(key)
                logger.info(f"Deleted terminal task ({task_id}) for user {user.id}. {initiator.value} initiated. Reason: {reason or '(unspecified)'}")

    async def _get_all_keys_for_pattern(self, pattern: str) -> List[str]:
        """
        Returns all Redis keys that match the pattern supplied.
        """

        keys = []

        async for key in self.redis.scan_iter(match=pattern, count=SCAN_COUNT):
            keys.append(key)

        return keys

    async def _get_task(self, key: str) -> Optional[PlaylistTaskStatus]:
        """
        Returns the task if it exists, or None if it doesn't.
        """

        raw = await self.redis.get(key)

        if raw:
            return PlaylistTaskStatus.model_validate_json(raw)

        return None

    async def _resolve_task_keys(self, user_id: int, task_id: uuid.UUID, verb: str) -> List[str]:
        """
        Resolves the Redis key(s) backing a user's task.

        A task_id should map to exactly one key; if more than one matches, all are
        returned and the caller decides how to handle it. Raises 404 if no key
        matches, so callers can treat a missing task uniformly.

        :param verb: Infinitive used in the 404 log (e.g. "cancel", "delete").
        """

        pattern = make_kind_agnostic_user_task_pattern(user_id, str(task_id))
        keys = await self._get_all_keys_for_pattern(pattern)

        if len(keys) == 0:
            self._raise_404_task_not_found(f"Attempted to {verb} a non-existent task with ID {task_id}.")

        return keys

    async def update_task_status(self, key: str, new_status: TaskStatus, initiator: Initiator, reason: Optional[str] = None) -> PlaylistTaskStatus:
        """
        Updates a task's status.

        - If the new status signals that the execution of the task ended (regardless of the actual ending type) then the task's done_at field is set to the current time.
        - Likewise, if the new status signals that the execution of the task hasn't ended (regardless of the actual status), the done_at field is cleared to avoid confusion.
        - If the reason is `None`, the task's status_reason field will be left as is, instead of being cleared.

        Returns the updated task after commiting the changes.
        """

        task = await self._get_task(key)

        if task is None:
            self._raise_404_task_not_found(f"Cannot update the status for task. No match for Redis key \"{key}\".")

        task.status = new_status

        if new_status in [TaskStatus.CANCELED, TaskStatus.FAILED, TaskStatus.FINISHED, TaskStatus.MARKED_FOR_DELETION]:
            task.done_at = int(time.time())
        else:
            task.done_at = None

        if reason:
            task.status_reason = reason

        await self.redis.set(key, task.model_dump_json(), ex=TTL_FINISHED)
        logger.info(f"Updated task ({task.task_id}). This was a {initiator.value} initiated action. Reasoning: {reason or "(unspecified)"}")

        return task
            
    def _raise_404_task_not_found(self, log_message: Optional[str]) -> None:
        if log_message:
            logger.info(log_message)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    async def delete_tasks_for_user(self, user: User, initiator: Initiator, reason: Optional[str] = None) -> None:
        """
        Permanently deletes all tasks belonging to the specified user.

        Terminal tasks are removed immediately; active tasks are marked
        MARKED_FOR_DELETION for the worker to clean up.
        """

        tasks = await self.get_all_tasks_for_user(user)

        for task in tasks:
            await self.delete_task(
                task_id=task.task_id,
                user=user,
                initiator=initiator,
                reason=reason,
            )

async def get_task_service() -> AsyncGenerator[TaskService, None]:
    redis = get_redis_instance()
    try:
        yield TaskService(redis)
    finally:
        await redis.aclose()
