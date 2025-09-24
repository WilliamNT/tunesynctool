from typing import Optional
import uuid
from fastapi import HTTPException, status
import redis.asyncio as redis
import time

from api.models.task import PlaylistTaskProgress, PlaylistTaskStatus, PlaylistTaskCreate, TaskStatus
from api.models.user import User
from api.core.config import config
from api.models.collection import Collection
from api.core.logging import logger

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
        redis_key = f"user_tasks:{details.kind}:{user.id}:{task_id}"
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
            value=job.model_dump_json()
        )

        await self.redis.rpush("user_tasks_queue", redis_key)

        return job

    async def get_playlist_transfer_status(self, task_id: str, user: User) -> PlaylistTaskProgress:
        task = await self.redis.get(f"playlist_transfer:{user.id}:{task_id}")
        await self.redis.aclose()

        return PlaylistTaskProgress.model_validate_json(task)
    
    async def handle_compiling_tasks_for_user(self, user: User) -> Collection[PlaylistTaskProgress]:
        tasks = []

        async for key in self.redis.scan_iter(f"user_tasks:*:{user.id}:*"):
            raw = await self.redis.get(key)

            if raw:
                task = PlaylistTaskStatus.model_validate_json(raw)
                tasks.append(task)

        return Collection(
            items=tasks
        )

    async def dispatch_task_cancellation(self, task_id: uuid.UUID, user: User) -> None:
        """
        Deletes the task from Redis to signal to the worker that took it to free it self up.
        """

        pattern = f"user_tasks:*:{user.id}:{task_id}"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

            if len(keys) == 2:
                break

        if len(keys) == 0:
            self._raise_404_task_not_found(f"User {user.id} attempted to delete a non-existent task with ID {task_id}.")

        if len(keys) > 1:
            logger.warning(f"Multiple Redis keys matched for pattern \"{pattern}\" but only one should exist. This is likely a bug, someone tampered with the Redis DB or a UUID collision happened (unlikely). Only the first match will be deleted! Keys found: {', '.join(keys)}")

        try:
            await self.redis.delete(keys[0])
        except Exception as e:
            logger.error(f"An error occurred while deleting task with key {task_id}. Error: {e}", exc_info=True)
            
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