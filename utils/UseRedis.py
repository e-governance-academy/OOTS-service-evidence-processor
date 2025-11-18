import json
import os

import redis
import redis.asyncio as Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL = os.getenv("REDIS_TTL", "86400")  # 1 day
TTL = TTL if TTL.isdigit() else int(TTL)


class UseRedisAsync:
    """A class for asynchronous Redis operations with type checking and error handling.
    Attributes:
        _redis_client: Redis async client instance
    """

    def __init__(self, redis_url: str | Redis.Redis | None = None):
        """Initialize Redis client with provided URL or default configuration.
        Args:
            redis_url: Redis connection URL or Redis client instance.
                      If None, uses default REDIS_URL from environment.
        Raises:
            redis.exceptions.ConnectionError: If Redis connection fails
        """
        try:
            if isinstance(redis_url, Redis.Redis):
                self._redis_client = redis_url
            else:
                url = redis_url if isinstance(redis_url, str) else REDIS_URL
                self._redis_client = Redis.from_url(url)
        except Exception as e:
            raise redis.exceptions.ConnectionError(f"Failed to connect to Redis: {e}")

    async def get_from_redis(self, key: str) -> dict | None:
        """Get and deserialize JSON data from Redis by key.
        Args:
            key: Redis key to retrieve data from
        Returns:
            Deserialized dictionary or None if key doesn't exist
        Raises:
            json.JSONDecodeError: If data cannot be decoded as JSON
        """
        data = await self._redis_client.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return json.loads(data, default=str)

    async def save_to_redis(self, key: str, data: dict) -> None:
        """Save dictionary as JSON to Redis with TTL.
        Args:
            key: Redis key to store data under
            data: Dictionary to serialize and store
        """
        await self._redis_client.set(key, json.dumps(data), ex=TTL)

    async def push_to_queue(self, queue_name: str, message: str) -> None:
        """Push message to Redis list queue.
        Args:
            queue_name: Name of the Redis list queue
            message: Message to push to the queue
        """
        await self._redis_client.lpush(queue_name, message)

    async def update_from_redis(self, key: str, data: dict) -> None:
        """Update existing dictionary in Redis with new data.
        Args:
            key: Redis key of dictionary to update
            data: Dictionary with new values to merge
        Raises:
            TypeError: If stored value is not a dictionary
        """
        d = await self.get_from_redis(key)
        if isinstance(d, dict):
            d.update(data)
        else:
            raise TypeError("Value in Redis is not a dictionary")
        await self.save_to_redis(key, d)

    @property
    def redis(self) -> Redis.Redis:
        """Get the Redis client instance.
        Returns:
            Redis client instance
        """
        return self._redis_client
