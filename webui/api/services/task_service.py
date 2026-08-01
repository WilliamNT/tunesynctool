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
from api.workers.utils.constants import TTL_QUEUED, TTL_FINISHED
from api.models.system import Initiator

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
        
        async for key in self.redis.scan_iter(pattern):
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
        
        :param task_id: UUID of the task
        :param user: User who owns the task
        """

        await self._cancel_tasks(
            task_ids=[task_id],
            user=user,
            initiator=Initiator.USER,
            reason="Cancelled by user."
        )

    async def _cancel_tasks(self, task_ids: List[uuid.UUID], user: User, initiator: Initiator, reason: Optional[str] = None) -> None:
        """
        Marks all specified tasks as cancelled.

        If the task IDs do not belong to the user, this will fail.

        :param task_ids: An array of task IDs to delete
        :param user: The user the tasks supposedly belong to
        :param initiator: Used for logging. Sets whether this action was initiated by the system or the user
        """

        if len(task_ids) == 0:
            logger.info(f"The {initiator.value} dispatched the cancellation of all tasks belonging to the user with ID {user.id} cancellation but there are none to cancel. Aborting.")
            return

        logger.info(f"The {initiator.value} marked {len(task_ids)} tasks belonging to user with ID {user.id} for cancellation. Workers may not react to this instantly, please be patient. Reason: {reason}")

        successfully_deleted = 0

        try:
            for task_id in task_ids:
                await self._cancel_task(
                    user_id=user.id,
                    task_id=task_id,
                    initiator=initiator,
                    reason=reason
                )
                successfully_deleted += 1
        except HTTPException:
            raise
        except Exception:
            logger.exception(f"Failed to delete {len(task_ids) - successfully_deleted} tasks for user with ID {user.id}.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong."
            )

    async def _cancel_task(self, user_id: int, task_id: uuid.UUID, initiator: Initiator, reason: Optional[str] = None) -> None:
        """
        Cancels the specified task.
        """

        pattern = make_kind_agnostic_user_task_pattern(user_id, str(task_id))
        _keys = await self._get_all_keys_for_pattern(pattern)

        if len(_keys) == 0:
            self._raise_404_task_not_found(f"Attempted to cancel a non-existent task with ID {task_id}." )

        if len(_keys) > 1:
            logger.warning(f"[task:{task_id}] Multiple Redis keys matched for pattern '{pattern}'. Only the first will be cancelled.")

        key = _keys[0]
        task = await self._get_task(key)

        # Task is already terminal; treat DELETE as clearing it from the user's task list.
        is_deleted = await self._purge_task_if_terminal(key, task)
        if is_deleted:
            logger.info(f"Deleted terminal task ({task_id}) for user {user_id}. This was a {initiator.value} initiated action. Reasoning: {reason or "(unspecified)"}")
            return

        await self.update_task_status(
            key=key,
            new_status=TaskStatus.CANCELED,
            initiator=initiator,
            reason=reason
        )

    async def _purge_task_if_terminal(self, key: str, task: PlaylistTaskStatus) -> bool:
        """
        Deletes the task from Redis if already finished. Otherwise nothing happens.
        
        Returns true if the task was deleted and false if not.
        """

        is_terminal = task.status not in [TaskStatus.RUNNING, TaskStatus.QUEUED, TaskStatus.ON_HOLD]

        if is_terminal:
            await self.redis.delete(key)

        is_deleted = await self._get_task(key) is None

        return is_deleted

    async def _get_all_keys_for_pattern(self, pattern: str) -> List[str]:
        """
        Returns all Redis keys that match the pattern supplied.
        """

        keys = []

        async for key in self.redis.scan_iter(match=pattern):
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
        Permanently deletes all tasks belonging to the specified user and notifies workers about it.
        """

        tasks = await self.get_all_tasks_for_user(user)

        await self._cancel_tasks(
            task_ids=[task.task_id for task in tasks],
            user=user,
            initiator=initiator,
            reason=reason
        )

async def get_task_service() -> AsyncGenerator[TaskService, None]:
    redis = get_redis_instance()
    try:
        yield TaskService(redis)
    finally:
        await redis.aclose()
