"""
Background Worker Entrypoint for Python RQ Daemon
"""

import logging
import sys

from plagiarism.core.config import get_settings
from plagiarism.core.logging import setup_logging
from plagiarism.jobs.queue import get_redis_connection

logger = logging.getLogger("plagiarism.worker")


def run_worker():
    """Starts the Python RQ worker loop listening on configured Redis queues."""
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, service_name="plagiarism-worker")

    logger.info(
        "Starting Plagiarism Platform background worker daemon",
        extra={"queue": settings.WORKER_QUEUE_NAME, "environment": settings.ENVIRONMENT}
    )

    redis_conn = get_redis_connection()
    if redis_conn is None:
        logger.error("Cannot start worker: Redis connection is unavailable")
        sys.exit(1)

    try:
        from rq import Connection, Queue, Worker
        with Connection(redis_conn):
            queues = [Queue(settings.WORKER_QUEUE_NAME)]
            worker = Worker(queues)
            logger.info("Worker registered and listening for queued tasks...")
            worker.work(with_scheduler=True)
    except Exception as e:
        logger.exception("Worker encountered a fatal error during execution", exc_info=e)
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
