import logging
import os

import redis.asyncio as aioredis

from apps.processor import processor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

redis_timeout = os.getenv("REDIS_TIMEOUT", 5)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = aioredis.from_url(redis_url)

# QUEUE_OUTCOMING = os.getenv("QUEUE_OUTCOMING", "oots:queue:outgoing")
QUEUE_INCOMING = os.getenv("QUEUE_INCOMING", "oots:queue:incoming")


async def process_evidence_requests():
    _logger.info("Evidence Processor запущено, прослуховування запитів...")

    running = True
    while running:
        obj = await redis_client.blpop(QUEUE_INCOMING, timeout=redis_timeout)
        i, message_id = obj if obj else (None, None)
        if not message_id:
            continue

        message_id = message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id
        _logger.info(f"Отримано запит з Redis: {message_id}")
        asyncio.create_task(processor(message_id))


if __name__ == "__main__":
    log_level = os.getenv("LOGGING_LEVEL", "INFO")
    log_format = os.getenv("LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_datefmt = os.getenv("LOGGING_DATE", "%Y-%m-%d %H:%M:%S")
    logging.basicConfig(
        format=log_format,
        datefmt=log_datefmt,
        level=log_level,
        handlers=[logging.StreamHandler()]
    )

    import asyncio

    _logger.info('Starting...')
    asyncio.run(process_evidence_requests())
