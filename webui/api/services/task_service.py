import uuid
import redis.asyncio as redis
import time

from api.models.task import PlaylistTaskProgress, PlaylistTaskStatus, PlaylistTransferCreate, TaskStatus
from api.models.user import User
from api.core.config import config
from api.models.collection import Collection

class TaskService:
    def __init__(self):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True
        )
        
    async def dispatch_playlist_transfer(self, details: PlaylistTransferCreate, user: User) -> PlaylistTaskStatus:
        """
        Attempts to transfer the specified playlist from the source provider to the target provider.
        Replication is not guaranteed to be 100% successful.
        
        This starts a long running task. Clients can poll for the progress of the transfer.
        """

        task_id = str(uuid.uuid4())
        redis_key = f"playlist_transfer:{user.id}:{task_id}"
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

        await self.redis.rpush("playlist_tasks_queue", redis_key)

        return job
    
    async def get_playlist_transfer_status(self, task_id: str, user: User) -> PlaylistTaskProgress:
        task = await self.redis.get(f"playlist_transfer:{user.id}:{task_id}")
        await self.redis.aclose()

        return PlaylistTaskProgress.model_validate_json(task)
    
    async def handle_compiling_tasks_for_user(self, user: User) -> Collection[PlaylistTaskProgress]:
        tasks = []

        async for key in self.redis.scan_iter(f"playlist_*:{user.id}:*"):
            raw = await self.redis.get(key)

            if raw:
                task = PlaylistTaskStatus.model_validate_json(raw)
                tasks.append(task)

        return Collection(
            items=tasks
        )

def get_task_service() -> TaskService:
    return TaskService()