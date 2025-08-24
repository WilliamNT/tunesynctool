import json
from typing import List, Optional
from redis.asyncio import Redis
from tunesynctool.exceptions import PlaylistNotFoundException
from tunesynctool.features import AsyncTrackMatcher
from tunesynctool.models.track import Track
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
from api.models.entity import EntityAssetsBase
from api.services.providers.base_provider import BaseProvider

async def check_if_task_was_deleted(task_id: str, redis: Redis) -> bool:
    result = await redis.get(task_id)
    if result is None:
        logger.warning(f"A worker detected that a task it was working on was deleted. Freeing up worker now.")

    return result is None

async def do_current_iteration(task_id: str, task: PlaylistTaskStatus, redis: Redis, source_tracks: List[Track], source_provider: BaseProvider, matcher: AsyncTrackMatcher, source_track: Track, user: User) -> Optional[Track]:
    task.status_reason = None
    task.status = TaskStatus.RUNNING
    await redis.set(task_id, task.model_dump_json())

    task.progress.handled += 1
    task.progress.in_queue = len(source_tracks) - task.progress.handled

    return await matcher.find_match(source_track)

async def get_track_assets(source_provider: BaseProvider, track: Track, user: User) -> EntityAssetsBase:
    try:
        return await asyncio.wait_for(
            source_provider.get_track_assets(track, user),
            timeout=15
        )
    except asyncio.TimeoutError:
        logger.warning(f"Fetching track assets from provider {source_provider.provider_name} for track {track.service_id} timed out, using fallback instead.")
        
        return EntityAssetsBase(
            cover_image=None
        )

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
    except Exception as e:
        logger.error(f"Task {task_id} can't be started because an error occured while fetching the source playlist. Reason: {e}")

        task.status = TaskStatus.FAILED
        task.status_reason = "An error occured."
        task.done_at = int(time.time())
        await redis.select(task_id, task.model_dump_json())
        raise
    
    try:
        source_tracks = await asyncio.wait_for(
            source_driver.get_playlist_tracks(playlist_id=source_playlist.service_id, limit=0),
            timeout=30
        )
    except asyncio.TimeoutError:
        logger.error(f"Task {task_id} can't be started because an error occured while fetching tracks in the source playlist. Reason: Fetching tracks timed out.")
        task.status = TaskStatus.FAILED
        task.status_reason = "An error occured."
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
        return

    if len(source_tracks) == 0:
        logger.info("Canceled playlist transfer. Reason: The source playlist does not contain any items.")
        task.status = TaskStatus.CANCELED
        task.status_reason = "No items to process."
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
        return

    matcher = AsyncTrackMatcher(target_driver)
    matches = []
    
    for source_track in source_tracks:
        if await check_if_task_was_deleted(task_id, redis):
            return
        
        if task.progress.handled % 10 == 0 and task.progress.handled != 0:
            task.status = TaskStatus.ON_HOLD
            task.status_reason = "Pausing transfer to avoid a rate limit."
            await redis.set(task_id, task.model_dump_json())
            await asyncio.sleep(5)
            
        try:
            result = await asyncio.wait_for(
                do_current_iteration(
                    task_id=task_id,
                    task=task,
                    redis=redis,
                    source_tracks=source_tracks,
                    source_provider=source_provider,
                    matcher=matcher,
                    source_track=source_track,
                    user=user
                ),
                timeout=300
            )

            if result:
                matches.append(result)
        except asyncio.TimeoutError:
            logger.warning(f"Finding a match for track {source_track.service_id} from {source_track.service_name} at provider {target_provider.provider_name} timed out. Skipping track.")


        assets = await get_track_assets(source_provider, source_track, user)
        task.progress.track = map_track_between_domain_model_and_response_model(source_track, source_provider.provider_name, assets)
        await redis.set(task_id, task.model_dump_json())
        
    if len(matches) == 0:
        logger.info("Canceled playlist transfer. Reason: Couldn't find any matches.")
        task.status = TaskStatus.CANCELED
        task.status_reason = "Couldn't find any matches."
        task.done_at = int(time.time())
        await redis.set(task_id, task.model_dump_json())
        return

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