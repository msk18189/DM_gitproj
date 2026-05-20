"""Optional cache layer — graceful when Redis is not configured."""
import os
from typing import Any, Dict

from utils.logging_config import get_logger

logger = get_logger("cache")

_REDIS_URL = os.getenv("REDIS_URL", "").strip()
_client = None
_init_attempted = False


def _get_client():
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True
    if not _REDIS_URL:
        return None
    try:
        import redis

        _client = redis.from_url(_REDIS_URL, decode_responses=True)
        _client.ping()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        _client = None
    return _client


def check_health() -> Dict[str, Any]:
    client = _get_client()
    if not _REDIS_URL:
        return {"status": "disabled", "message": "Redis not configured (optional)"}
    if client is None:
        return {"status": "unhealthy", "message": "Redis configured but unreachable"}
    try:
        client.ping()
        return {"status": "healthy", "message": "Redis connected"}
    except Exception:
        return {"status": "unhealthy", "message": "Redis ping failed"}
