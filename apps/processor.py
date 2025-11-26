import logging
import os
from urllib.parse import urlparse

from apps.route import route
from utils.EDMRequestParsing import EDMRequestParsing
from utils.UseRedis import UseRedisAsync

_logger = logging.getLogger(__name__)

QUEUE_OUTCOMING = os.getenv("QUEUE_OUTCOMING", "oots:queue:outgoing")
QUEUE_INCOMING = os.getenv("QUEUE_INCOMING", "oots:queue:incoming")
URL_PREVIEW = os.getenv("PREVIEW_URL", "http://localhost:8000/")
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

UseRedis = UseRedisAsync(redis_url)


async def processor(message_id: str):
    xml_request = await UseRedis.get_from_redis(f"oots:message:request:edm:{message_id}")
    if isinstance(xml_request, list):
        edm_request = EDMRequestParsing(xml_request[0]["content"])
    else:
        _logger.error(f"Щось пішло не так читай запит")
        return None

    t = edm_request.evidenceTypeClassification
    proc_queue = await UseRedis.get_from_redis(f'oots:evidencetype:{t.split("/")[-1]}')

    if proc_queue:
        await UseRedis.push_to_queue(proc_queue, f"{message_id}")
    else:
        evidence, evidence_metadata, preview = route(edm_request)

        evidence.get_evidence(edm_request)

        await UseRedis.save_to_redis(f"oots:message:response:evidence:{message_id}", evidence.to_redis)
        await UseRedis.push_to_queue(QUEUE_OUTCOMING, f"{message_id}")

    return None
