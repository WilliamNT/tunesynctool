from redis.asyncio import Redis
from tunesynctool.exceptions import PlaylistNotFoundException
from tunesynctool.features import AsyncTrackMatcher
import asyncio
import time

from api.models.task import PlaylistTaskStatus
from api.core.logging import logger
from api.models.task import TaskStatus
from api.helpers.mapping import map_track_between_domain_model_and_response_model
from api.services.providers.provider_factory import ProviderFactory
from api.services.credentials_service import get_credentials_service
from api.models.user import User
from api.core.database import get_session

async def handle_playlist_transfer(task: PlaylistTaskStatus, task_id: str, user: User, redis: Redis) -> None:
    logger.info(f"Transfering playlist {task.arguments.from_playlist} from {task.arguments.from_provider} to {task.arguments.to_provider}.")

    async for session in get_session():
        credentials_service = get_credentials_service(session)

        try:
            source_provider = ProviderFactory.create(task.arguments.from_provider, credentials_service)
            target_provider = ProviderFactory.create(task.arguments.to_provider, credentials_service)
            source_driver = await source_provider._get_driver(user)
            target_driver = await target_provider._get_driver(user)
        except Exception as e:
            logger.error(F"Task {task_id} can't be started. Reason: {e}")

            task.status = TaskStatus.FAILED
            task.status_reason = "An error occured."
            task.done_at = int(time.time())
            await redis.set(task_id, task.model_dump_json())

            return
        
        break
    
    try:
        source_playlist = await source_driver.get_playlist(playlist_id=task.arguments.from_playlist)
    except PlaylistNotFoundException:
        logger.error(f"Task {task_id} can't be started because the supplied source playlist {task.arguments.from_playlist} doesn't exist at provider {task.arguments.from_provider}.")
        
        task.status = TaskStatus.CANCELED
        task.status_reason = "Playlist does not exist."
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
        
        return
    
    source_tracks = await source_driver.get_playlist_tracks(playlist_id=source_playlist.service_id, limit=0)

    if len(source_tracks) == 0:
        logger.info("Cancelled playlist transfer. Reason: The source playlist does not contain any items.")
        task.status = TaskStatus.CANCELED
        task.status_reason = "No items to process."
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
        return

    matcher = AsyncTrackMatcher(target_driver)
    matches = []
    
    for source_track in source_tracks:
        if task.progress.handled % 10 == 0 and task.progress.handled != 0:
            task.status = TaskStatus.ON_HOLD
            task.status_reason = "Pausing transfer to avoid a rate limit."
            await redis.set(task_id, task.model_dump_json())
            await asyncio.sleep(5)

        task.status_reason = None
        task.status = TaskStatus.RUNNING
        await redis.set(task_id, task.model_dump_json())

        task.progress.handled += 1
        task.progress.in_queue = len(source_tracks) - task.progress.handled

        assets = await source_provider.get_track_assets(source_track, user)
        task.progress.track = map_track_between_domain_model_and_response_model(source_track, task.arguments.from_provider, assets)

        await redis.set(task_id, task.model_dump_json())

        result = await matcher.find_match(source_track)

        if result:
            matches.append(result)

    try:
        target_playlist = await target_driver.create_playlist(source_playlist.name)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.status_reason = "Couldn't create playlist."
        task.done_at = int(time.time())
        logger.error(f"Failure while creating new playlist. Reason: {e}")
        await redis.set(task_id, task.model_dump_json())
        return
        
    try:        
        await target_driver.add_tracks_to_playlist(
            playlist_id=target_playlist.service_id,
            track_ids=[track.service_id for track in matches]
        )
        
        logger.info(f"Successfuly finished transfer of playlist from {source_provider.provider_name} to {target_provider.provider_name}.")
        task.status = TaskStatus.FINISHED
        task.status_reason = None
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.status_reason = "An error occured."
        task.done_at = int(time.time())
        logger.error(f"Failure while inserting tracks into playlist. Reason: {e}")
        await redis.set(task_id, task.model_dump_json())