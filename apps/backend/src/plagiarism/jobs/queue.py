"""
Redis and Python RQ Queue Configuration
"""

import logging

from plagiarism.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_connection():
    """Returns singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            settings = get_settings()
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=5
            )
        except ImportError:
            logger.warning("Redis package not installed; background jobs queue running in mock mode")
            return None
    return _redis_client


def get_queue(name: str | None = None):
    """Returns an RQ Queue instance connected to Redis."""
    try:
        from rq import Queue
        settings = get_settings()
        queue_name = name or settings.WORKER_QUEUE_NAME
        conn = get_redis_connection()
        if conn is None:
            raise RuntimeError("Redis connection is unavailable")
        return Queue(queue_name, connection=conn)
    except ImportError:
        raise RuntimeError("Python RQ package is not installed")


async def check_redis_health() -> bool:
    """Executes a ping to Redis to verify connectivity."""
    try:
        conn = get_redis_connection()
        if conn is None:
            return False
        # Redis sync client ping
        return bool(conn.ping())
    except Exception:
        return False


async def close_redis_connection() -> None:
    """Closes the singleton Redis client connection on shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None

