from redis.asyncio import Redis
import asyncio

from api.core.logging import logger
from api.core.config import config
from api.models.task import PlaylistTaskStatus, TaskStatus, TaskKind
from api.workers.handlers.playlist_transfer_handler import handle_playlist_transfer
from api.services.user_service import UserService
from api.core.database import get_session

async def worker_dispatcher(worker_id: int):
    logger.info(f"Worker {worker_id} is now running.")

    redis = Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True
    )

    while True:
        next_in_queue = await redis.blpop("user_tasks_queue", timeout=5)
        if not next_in_queue:
            continue

        task_id = next_in_queue[1]

        logger.info(f"Worker {worker_id} noticed an unhandled task in queue (Redis key: {task_id}). Taking care of it now...")

        unparsed_task = await redis.get(task_id)
        if not unparsed_task:
            logger.error(f"Worker {worker_id} found no task data for Redis key: {task_id}. Skipping...")
            continue

        task = PlaylistTaskStatus.model_validate_json(unparsed_task)

        if task.status != TaskStatus.QUEUED:
            continue

        task.status = TaskStatus.RUNNING
        await redis.set(task_id, task.model_dump_json())

        # user_tasks:TASK_KIND:USER_ID:TASK_ID
        task_kind = task_id.split(":")[1]
        user_id = task_id.split(":")[2]

        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_by_id(int(user_id))
            break

        match task_kind:
            case TaskKind.USER_INITIATED_PLAYLIST_TRANSFER:
                await handle_playlist_transfer(task=task, task_id=task_id, user=user, redis=redis)
            case _:
                logger.error(f"Unrecognized task type \"{task_kind}\". Task ID: {task_id}")
        
        await asyncio.sleep(1)