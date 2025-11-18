import logging
import os
from urllib.parse import urlparse

from apps.route import route
from utils.EDMRequestParsing import EDMRequestParsing
from utils.UseRedis import UseRedisAsync

_logger = logging.getLogger(__name__)

QUEUE_OUTCOMING = os.getenv("QUEUE_OUTCOMING", "oots:queue:outgoing")
QUEUE_INCOMING = os.getenv("QUEUE_INCOMING", "oots:queue:incoming")
URL_PREVIEW = os.getenv("URL_PREVIEW", "http://localhost:8000/")
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

UseRedis = UseRedisAsync(redis_url)


async def processor(message_id: str):
    xml_request = await UseRedis.get_from_redis(f"oots:message:request:edm:{message_id}")
    if isinstance(xml_request, list):
        edm_request = EDMRequestParsing(xml_request[0]["content"])
    else:
        _logger.error(f"Щось пішло не так читай запит")
        return None

    # if edm_request.is_second:
    #     url = edm_request.slot_text('PreviewLocation')
    #     url_path = urlparse(url).path
    #
    #     edm = await UseRedis.get_from_redis(f"oots:message:request:edm:{url_path}")
    #     if edm:
    #         await UseRedis.save_to_redis(f"oots:message:request:preview:{url_path}", True )
    #         _logger.info(f"Отримали другий запит на доказ: {url_path}")
    #     _logger.error(f"Отримали щось не дуже схоже на правду")
    #     return None

    evidence, evidence_metadata, preview = route(edm_request)

    evidence.get_evidence(edm_request)

    await UseRedis.save_to_redis(f"oots:message:response:evidence:{message_id}", evidence.to_redis)
    await UseRedis.push_to_queue(QUEUE_OUTCOMING, f"{message_id}")

    return None
