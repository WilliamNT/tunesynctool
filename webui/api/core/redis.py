from typing import AsyncGenerator

from redis.asyncio import Redis

from api.core.config import config


def get_redis_instance() -> Redis:
    """
    Get a direct Redis client instance for internal use.
    """

    return Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True
    )


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Get a Redis client for FastAPI dependencies.
    """

    redis = get_redis_instance()
    try:
        yield redis
    finally:
        await redis.aclose()
