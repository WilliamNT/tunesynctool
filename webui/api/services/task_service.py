from typing import Optional
import uuid
from fastapi import HTTPException, status
import redis.asyncio as redis
import time

from api.models.task import PlaylistTaskProgress, PlaylistTaskStatus, PlaylistTaskCreate, TaskStatus, TaskKind
from api.models.user import User
from api.core.config import config
from api.models.collection import Collection
from api.core.logging import logger
from api.workers.keys import make_task_key, make_user_tasks_pattern, make_task_queue_name, TTL_QUEUED, TTL_FINISHED

class TaskService:
    def __init__(self):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True
        )
        
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
    
    async def handle_compiling_tasks_for_user(self, user: User) -> Collection[PlaylistTaskStatus]:
        tasks = []
        pattern = make_user_tasks_pattern(user.id)

        async for key in self.redis.scan_iter(pattern):
            raw = await self.redis.get(key)

            if raw:
                task = PlaylistTaskStatus.model_validate_json(raw)
                tasks.append(task)

        return Collection(
            items=tasks
        )

    async def dispatch_task_cancellation(self, task_id: uuid.UUID, user: User) -> None:
        """
        Marks a task as cancelled. The worker will detect this and stop processing.
        
        :param task_id: UUID of the task
        :param user: User who owns the task
        """

        pattern = make_user_tasks_pattern(user.id).replace("*:*", f"*:{task_id}")
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

            if len(keys) == 2:
                break

        if len(keys) == 0:
            self._raise_404_task_not_found(f"User {user.id} attempted to cancel a non-existent task with ID {task_id}.")

        if len(keys) > 1:
            logger.warning(f"[task:{task_id}] Multiple Redis keys matched for pattern '{pattern}'. Only first will be cancelled.")

        try:
            raw = await self.redis.get(keys[0])

            if raw:
                task = PlaylistTaskStatus.model_validate_json(raw)
                task.status = TaskStatus.CANCELED
                task.status_reason = "Cancelled by user."
                task.done_at = int(time.time())
                
                await self.redis.set(keys[0], task.model_dump_json(), ex=TTL_FINISHED)
                logger.info(f"[task:{task_id}] Task cancelled by user {user.id}")
        except Exception as e:
            logger.error(f"[task:{task_id}] Error cancelling task: {e}", exc_info=True)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong."
            )
    
    def _raise_404_task_not_found(self, log_message: Optional[str]) -> None:
        if log_message:
            logger.info(log_message)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

def get_task_service() -> TaskService:
    return TaskService()