from typing import List, Optional, Set
from tunesynctool.exceptions import PlaylistNotFoundException
from tunesynctool.features import AsyncTrackMatcher
from tunesynctool.models import Playlist, Track
from tunesynctool.utilities.collections import batch
from tunesynctool.drivers.async_service_driver import AsyncWrappedServiceDriver
import asyncio
from contextlib import AsyncExitStack

from api.models.task import PlaylistTaskStatus
from api.core.logging import logger
from api.helpers.mapping import map_track_between_domain_model_and_response_model
from api.services.providers.provider_factory import ProviderFactory
from api.services.credentials_service import get_credentials_service
from api.models.user import User
from api.core.database import get_session_instance
from api.models.entity import EntityAssetsBase
from api.services.providers.base_provider import BaseProvider
from api.workers.utils.task_status import (
    report_task_failure,
    report_task_cancellation,
    report_task_on_hold,
    report_task_finished,
    report_task_as_running,
    check_if_task_is_dormant,
    save_task,
    sleep_unless_dormant
)
from api.workers.utils.context import WorkerContext

async def do_current_iteration(
    context: WorkerContext,
    source_tracks: List[Track],
    matcher: AsyncTrackMatcher,
    source_track: Track
) -> Optional[Track]:
    await report_task_as_running(
        redis=context.redis,
        task=context.current_task,
        redis_key=context.current_redis_key
    )

    context.current_task.progress.handled += 1
    context.current_task.progress.in_queue = len(source_tracks) - context.current_task.progress.handled

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

class PlaylistPullException(Exception):
    """When pulling a playlist via the driver failed for a known reason."""

    def __init__(self, message="Error while trying to get playlist."):
        super().__init__(message)

async def pull_playlist(context: WorkerContext, driver: AsyncWrappedServiceDriver, playlist_id: str, provider_name: str) -> Playlist:
    try:
        return await driver.get_playlist(playlist_id=playlist_id)
    except PlaylistNotFoundException:
        logger.error(f"Error while preparing task {context.current_task.task_id}. The supplied playlist {playlist_id} doesn't exist at provider {provider_name}.")
        await report_task_cancellation(
            redis=context.redis,
            task=context.current_task,
            redis_key=context.current_redis_key,
            reason="Playlist does not exist."
        )

        raise PlaylistPullException(f"Could not fetch playlist {playlist_id} via provider {provider_name} because the provider reported that the playlist does not exist.")
    except Exception as e:
        logger.error(f"Error while preparing task {context.current_task.task_id}. An error occured while fetching the playlist. Details: {e}")
        await report_task_failure(
            redis=context.redis,
            task=context.current_task,
            redis_key=context.current_redis_key,
        )

        raise

async def match_tracks(
    context: WorkerContext,
    source_provider: BaseProvider,
    target_provider: BaseProvider,
    user: User,
    target_driver: AsyncWrappedServiceDriver,
    source_tracks: List[Track],
    existing_target_ids: Optional[Set[str]] = None,
) -> List[Track]:
    if existing_target_ids is None:
        existing_target_ids = set()

    matcher = AsyncTrackMatcher(target_driver)
    matches = []

    for source_track in source_tracks:
        if await check_if_task_is_dormant(context.redis, context.current_redis_key):
            logger.info(f"Task {context.current_task.task_id} was cancelled by user.")
            return matches
    
        if context.current_task.progress.handled % 10 == 0 and context.current_task.progress.handled != 0:
            await report_task_on_hold(
                redis=context.redis,
                task=context.current_task,
                redis_key=context.current_redis_key,
                reason="Pausing to avoid a rate limit."
            )

            if await sleep_unless_dormant(context.redis, context.current_redis_key, 5):
                logger.info(f"Task {context.current_task.task_id} was cancelled by user.")
                return matches
        
        result = None
        try:
            result = await asyncio.wait_for(
                do_current_iteration(
                    context=context,
                    source_tracks=source_tracks,
                    matcher=matcher,
                    source_track=source_track
                ),
                timeout=300
            )

            if result and result.service_id not in existing_target_ids:
                matches.append(result)
                existing_target_ids.add(result.service_id)

        except asyncio.TimeoutError:
            logger.warning(f"Finding a match for track {source_track.service_id} from {source_track.service_name} at provider {target_provider.provider_name} timed out. Skipping track.")

        assets = await get_track_assets(source_provider, source_track, user)
        context.current_task.progress.track = map_track_between_domain_model_and_response_model(source_track, context.current_task.arguments.from_provider, assets)

        await save_task(
            redis=context.redis,
            task=context.current_task,
            redis_key=context.current_redis_key,
            use_finished_ttl=False
        )

    return matches

async def handle_playlist_transfer(context: WorkerContext, user: User) -> None:
    task = context.current_task
    redis = context.redis
    redis_key = context.current_redis_key
    is_sync = bool(task.arguments.to_playlist)
    mode_label = "sync" if is_sync else "transfer"

    logger.info(f"{mode_label.capitalize()}ing playlist {task.arguments.from_playlist} from {task.arguments.from_provider} to {task.arguments.to_provider}.")

    async with await get_session_instance() as session, AsyncExitStack() as driver_stack:
        credentials_service = get_credentials_service(session)

        try:
            source_provider = ProviderFactory.create(task.arguments.from_provider, credentials_service)
            source_driver = await driver_stack.enter_async_context(await source_provider._get_driver(user))

            target_provider = None
            target_driver = None

            if task.arguments.from_provider == task.arguments.to_provider:
                target_provider = source_provider
                target_driver = source_driver
            else:
                target_provider = ProviderFactory.create(task.arguments.to_provider, credentials_service)
                target_driver = await driver_stack.enter_async_context(await target_provider._get_driver(user))
        except Exception as e:
            logger.error(f"Task {task.task_id} can't be started. Reason: {e}")
            await report_task_failure(
                redis=redis,
                task=task,
                redis_key=redis_key
            )

            return

        try:
            source_playlist = await pull_playlist(
                context=context,
                driver=source_driver,
                playlist_id=task.arguments.from_playlist,
                provider_name=source_provider.provider_name,
            )
        except PlaylistPullException:
            return

        try:
            source_tracks = await asyncio.wait_for(
                source_driver.get_playlist_tracks(playlist_id=source_playlist.service_id, limit=0),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.error(f"Task {task.task_id} can't be started because an error occured while fetching tracks in the source playlist. Reason: Fetching tracks timed out.")
            await report_task_failure(
                redis=redis,
                task=task,
                redis_key=redis_key,
            )

            return

        if len(source_tracks) == 0:
            logger.info(f"Canceled playlist {mode_label}. Reason: The source playlist does not contain any items.")
            await report_task_cancellation(
                redis=redis,
                task=task,
                redis_key=redis_key,
                reason="Playlist is empty."
            )

            return

        target_playlist = None
        existing_target_track_ids: Set[str] = set()

        if is_sync:
            try:
                target_playlist = await pull_playlist(
                    context=context,
                    driver=target_driver,
                    playlist_id=task.arguments.to_playlist,
                    provider_name=target_provider.provider_name,
                )
            except PlaylistPullException:
                return

            try:
                target_tracks = await asyncio.wait_for(
                    target_driver.get_playlist_tracks(playlist_id=target_playlist.service_id, limit=0),
                    timeout=30
                )
            except asyncio.TimeoutError:
                logger.error(f"Task {task.task_id} can't fetch target playlist tracks. Reason: Fetching tracks timed out.")
                await report_task_failure(
                    redis=redis,
                    task=task,
                    redis_key=redis_key,
                )
                return

            existing_target_track_ids = {t.service_id for t in target_tracks}

            # Filter out tracks already present in the target playlist
            tracks_to_process = []
            processed_target_tracks = set()

            for source_track in source_tracks:
                match_found = False
                for target_track in target_tracks:
                    if target_track in processed_target_tracks:
                        continue
                    if source_track.matches(target_track):
                        match_found = True
                        processed_target_tracks.add(target_track)
                        break
                if not match_found:
                    tracks_to_process.append(source_track)

            if len(tracks_to_process) == 0:
                logger.info(f"Task {task.task_id}: Target playlist {target_playlist.name} is already up to date. Sync complete.")
                await report_task_finished(
                    redis=redis,
                    task=task,
                    redis_key=redis_key
                )
                return

            logger.info(f"Task {task.task_id}: {len(tracks_to_process)} missing tracks to sync out of {len(source_tracks)} source tracks.")
        else:
            tracks_to_process = source_tracks

        matches = await match_tracks(
            context=context,
            source_provider=source_provider,
            target_provider=target_provider,
            user=user,
            target_driver=target_driver,
            source_tracks=tracks_to_process,
            existing_target_ids=existing_target_track_ids,
        )

        if len(matches) == 0:
            logger.info(f"Canceled playlist {mode_label}. Reason: Couldn't find any matches.")
            await report_task_cancellation(
                redis=redis,
                task=task,
                redis_key=redis_key,
                reason="Couldn't find any matches."
            )

            return

        if task.arguments.is_dry_run:
            logger.info("Skipping playlist creation and/or track insertion because the current task is a dry run. Task will be marked as successful.")
            await report_task_finished(
                redis=redis,
                task=task,
                redis_key=redis_key,
            )

            return

        # For transfer mode (when to_playlist is not specified), create the playlist now after matches are confirmed
        if not is_sync:
            try:
                target_playlist = await target_driver.create_playlist(source_playlist.name)
            except Exception as e:
                logger.error(f"Failure while creating new playlist. Reason: {e}")
                await report_task_failure(
                    redis=redis,
                    task=task,
                    redis_key=redis_key,
                    reason="Couldn't create playlist."
                )

                return

        if not target_playlist:
            logger.error("Target playlist should exist but doesn't. This is a bug!")
            await report_task_failure(
                redis=redis,
                task=task,
                redis_key=redis_key,
                reason="Target playlist is undefined."
            )

            return
        
        try:
            await insert_tracks_into_playlist(
                playlist_id=target_playlist.service_id,
                tracks=matches,
                driver=target_driver,
                context=context,
            )

            if await check_if_task_is_dormant(redis, redis_key):
                return
            
            logger.info(f"Successfully finished {mode_label} of playlist from {source_provider.provider_name} to {target_provider.provider_name}.")
            await report_task_finished(
                redis=redis,
                task=task,
                redis_key=redis_key,
            )

        except Exception as e:
            logger.error(f"Failure while inserting tracks into playlist. Reason: {e}")
            await report_task_failure(
                redis=redis,
                task=task,
                redis_key=redis_key,
            )

async def insert_tracks_into_playlist(playlist_id: str, tracks: List[Track], driver: AsyncWrappedServiceDriver, context: WorkerContext) -> None:
    for chunked_ids in batch([track.service_id for track in tracks], 25):
        if await check_if_task_is_dormant(context.redis, context.current_redis_key):
            return

        await driver.add_tracks_to_playlist(
            playlist_id=playlist_id,
            track_ids=chunked_ids
        )

        await report_task_on_hold(
            redis=context.redis,
            task=context.current_task,
            redis_key=context.current_redis_key,
            reason="Pausing to avoid a rate limit."
        )
        if await sleep_unless_dormant(context.redis, context.current_redis_key, 3):
            return
