from typing import List, Optional
from sqlmodel import select
from tunesynctool.drivers import AsyncWrappedServiceDriver
from tunesynctool.models.playlist import Playlist
from tunesynctool.models.track import Track
from redis.asyncio import Redis
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import config
from api.core.database import get_session_instance
from api.models.track import CachedTrackProviderMapping, CachedTrack
from api.core.logging import logger

class AsyncCachedDriver(AsyncWrappedServiceDriver):
    """
    Extends the original to stay compatible, however adds caching via Redis and DB to help avoid rate limits and api calls.
    """

    _db: Optional[AsyncSession] = None

    def __init__(self, base: AsyncWrappedServiceDriver):
        super().__init__(base.sync_driver)

        self.base = base
        self.redis = Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True
        )

    async def __aenter__(self) -> "AsyncCachedDriver":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    async def close(self) -> None:
        """Clean up resources - close database session and Redis connection."""
        if self._db:
            await self._db.close()
            self._db = None
        await self.redis.aclose()

    async def get_db(self) -> AsyncSession:
        if not self._db:
            self._db = await get_session_instance()

        return self._db

    def _deserialize_track(self, cached_data: str) -> Track:
        raw = json.loads(cached_data)
        return Track.deserialize(raw)
    
    def _serialize_track(self, track: Track) -> str:
        return json.dumps(track.serialize())

    def _deserialize_track_array(self, cached_data: str) -> List[Track]:
        raw_tracks = json.loads(cached_data)

        return [
            Track.deserialize(raw_track) for raw_track in raw_tracks
        ]
    
    def _serialize_track_array(self, tracks: List[Track]) -> str:
        return json.dumps([
            track.serialize() for track in tracks
        ])
    
    def _deserialize_playlist(self, cached_data: str) -> Playlist:
        raw = json.loads(cached_data)
        return Playlist.deserialize(raw)
    
    def _serialize_playlist(self, playlist: Playlist) -> str:
        return json.dumps(playlist.serialize())
    
    def _deserialize_playlist_array(self, cached_data: str) -> List[Playlist]:
        raw_playlists = json.loads(cached_data)

        return [
            Playlist.deserialize(raw_playlist) for raw_playlist in raw_playlists
        ]
    
    def _serialize_playlist_array(self, playlists: List[Playlist]) -> str:
        return json.dumps([
            playlist.serialize() for playlist in playlists
        ])
    
    def normalize_query(self, query: str) -> str:
        query = query.strip().lower()
        query = re.sub(r"\s+", "_", query)
        query = re.sub(r"[^\w_]", "", query)

        return query
    
    async def get_playlist(self, playlist_id: str) -> Playlist:
        key = f"provider_cache:{self.base.service_name}:playlists:playlist_id#{(playlist_id)}"
        cached = await self.redis.get(key)
        if cached:
            return self._deserialize_playlist(cached)
        
        result = await self.base.get_playlist(
            playlist_id=playlist_id,
        )
        
        await self.redis.set(key, self._serialize_playlist(result), ex=300)
        return result
    
    async def get_track(self, track_id: str) -> Track:
        db = await self.get_db()
        query = await db.execute(
            select(CachedTrack)
            .join(CachedTrackProviderMapping)
            .where(
                CachedTrackProviderMapping.track_id == track_id,
                CachedTrackProviderMapping.provider == self.base.service_name,
            )
        )

        cached = query.scalar_one_or_none()

        if cached:
            return Track(
                title=cached.title,
                album_name=cached.album_name,
                primary_artist=cached.author,
                additional_artists=cached.collaborators,
                duration_seconds=cached.duration,
                track_number=cached.track_number,
                release_year=cached.release_year,
                isrc=cached.isrc,
                musicbrainz_id=cached.musicbrainz,
                service_id=track_id,
                service_name=self.base.service_name
            )
        
        result = await self.base.get_track(
            track_id=track_id,
        )

        if result:
            # Cache in DB
            new_cached = CachedTrack(
                title=result.title,
                album_name=result.album_name,
                author=result.primary_artist,
                collaborators=result.additional_artists,
                duration=result.duration_seconds,
                track_number=result.track_number,
                release_year=result.release_year,
                isrc=result.isrc,
                musicbrainz=result.musicbrainz_id
            )
            db.add(new_cached)
            await db.commit()
            await db.refresh(new_cached)

            mapping = CachedTrackProviderMapping(
                track_id=new_cached.id,
                provider=self.base.service_name,
                provider_track_id=track_id
            )
            db.add(mapping)
            await db.commit()

        return result
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[Track]:
        key = f"provider_cache:{self.base.service_name}:search_results:query#{(self.normalize_query(query))}:limit#{limit}"
        cached = await self.redis.get(key)
        if cached:
            return self._deserialize_track_array(cached)
        
        results = await self.base.search_tracks(
            query=query,
            limit=limit
        )
        
        await self.redis.set(key, self._serialize_track_array(results), ex=3600) # 1 hour
        return results

    async def get_track_by_isrc(self, isrc: str) -> Optional[Track]:
        """
        Retrieve a track by its ISRC, using DB cache when available.
        Falls back to the base driver's API call if not cached.
        
        :param isrc: The International Standard Recording Code to look up.
        :return: The matching Track or None if not found.
        """
        return await self._get_track_by_isrc_with_cache(isrc)
    
    async def _get_track_by_isrc_with_cache(self, isrc: str) -> Optional[Track]:
        """
        Internal method to look up a track by ISRC using the DB cache.
        
        First checks if a track with the given ISRC exists in the cache for this provider.
        If found, returns the cached track. Otherwise, fetches from the base driver's API
        and caches the result.
        
        :param isrc: The ISRC to look up.
        :return: The matching Track or None if not found.
        """
        db = await self.get_db()
        
        # Query for cached track with matching ISRC AND provider mapping
        query = await db.execute(
            select(CachedTrack, CachedTrackProviderMapping.provider_track_id)
            .join(CachedTrackProviderMapping, CachedTrackProviderMapping.track_id == CachedTrack.id)
            .where(
                CachedTrack.isrc == isrc,
                CachedTrackProviderMapping.provider == self.base.service_name,
            )
        )

        result = query.first()
        
        if result is not None:
            cached_track, provider_track_id = result
            logger.debug(f"Cache hit for ISRC {isrc} at provider {self.base.service_name}")
            return Track(
                title=cached_track.title,
                album_name=cached_track.album_name,
                primary_artist=cached_track.author,
                additional_artists=cached_track.collaborators,
                duration_seconds=cached_track.duration,
                track_number=cached_track.track_number,
                release_year=cached_track.release_year,
                isrc=cached_track.isrc,
                musicbrainz_id=cached_track.musicbrainz,
                service_id=provider_track_id,
                service_name=self.base.service_name
            )
        
        # Cache miss - fetch from API
        logger.debug(f"Cache miss for ISRC {isrc} at provider {self.base.service_name}, fetching from API")
        api_result = await self.base.get_track_by_isrc(
            isrc=isrc,
        )

        if api_result:
            # Cache the result in DB
            new_cached = CachedTrack(
                title=api_result.title,
                album_name=api_result.album_name,
                author=api_result.primary_artist,
                collaborators=api_result.additional_artists,
                duration=api_result.duration_seconds,
                track_number=api_result.track_number,
                release_year=api_result.release_year,
                isrc=api_result.isrc,
                musicbrainz=api_result.musicbrainz_id
            )
            db.add(new_cached)
            await db.commit()
            await db.refresh(new_cached)

            mapping = CachedTrackProviderMapping(
                track_id=new_cached.id,
                provider=self.base.service_name,
                provider_track_id=api_result.service_id
            )
            db.add(mapping)
            await db.commit()
            logger.debug(f"Cached track {api_result.service_id} with ISRC {isrc} for provider {self.base.service_name}")

        return api_result