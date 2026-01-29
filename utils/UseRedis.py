import logging
import json
import os
from typing import Awaitable, cast, Any

import redis
from redis.asyncio import Redis

_logger = logging.getLogger(__name__)

QUEUE_OUTCOMING = os.getenv("QUEUE_OUTCOMING")
QUEUE_INCOMING = os.getenv("QUEUE_INCOMING")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL = int(os.getenv("REDIS_TTL", "86400"))  # 1 day


class UseRedisAsync:
    def __init__(self, redis_url: str | Redis | None = None):
        try:
            if isinstance(redis_url, Redis):
                self._redis_client = redis_url
            else:
                url = redis_url if isinstance(redis_url, str) else REDIS_URL
                self._redis_client = Redis.from_url(url)
        except Exception as e:
            raise redis.exceptions.ConnectionError(f"Failed to connect to Redis: {e}")

    async def get_from_redis(self, key: str) -> dict | None:
        data = await self._redis_client.get(key)
        _logger.debug(f"Get data: {key} datatype: {type(data)}")
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return json.loads(data, default=str)

    async def get_raw_from_redis(self, key: str) -> bytes | None:
        data = await self._redis_client.get(key)
        _logger.debug(f"Get raw data: {key} datatype: {type(data)}")
        return data if isinstance(data, bytes) else None

    async def save_to_redis(self, key: str, data: dict[Any, Any] | list | str) -> None:
        _logger.debug(f"Saving data to Redis: {key} datatype: {type(data)}")
        await self._redis_client.set(key, json.dumps(data, default=str), ex=TTL)

    async def save_raw_to_redis(self, key: str, data: bytes) -> None:
        _logger.debug(f"Saving raw data to Redis: {key} datatype: {type(data)}")
        await self._redis_client.set(key, data, ex=TTL)

    async def push_to_queue(self, queue_name: str, message: str) -> None:
        await cast(Awaitable[int], self._redis_client.lpush(queue_name, message))

    async def update_from_redis(self, key: str, data: dict) -> None:
        d = await self.get_from_redis(key)
        if isinstance(d, dict):
            d.update(data)
        else:
            raise TypeError("Value in Redis is not a dictionary")
        await self.save_to_redis(key, d)

    @property
    def redis(self) -> Redis:
        return self._redis_client

    async def close(self) -> None:
        """Close the Redis connection"""
        _logger.debug("Closing Redis connection")
        await self._redis_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
