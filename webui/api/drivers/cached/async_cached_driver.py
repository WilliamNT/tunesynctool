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

    async def get_track_by_isrc(self, isrc: str) -> Track:
        key = f"provider_cache:{self.base.service_name}:tracks:isrc#{(isrc)}"
        cached = await self.redis.get(key)
        if cached:
            return self._deserialize_track(cached)
        
        result = await self.base.get_track_by_isrc(
            isrc=isrc,
        )
        
        await self.redis.set(key, self._serialize_track(result))
        return result