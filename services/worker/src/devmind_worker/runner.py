import asyncio
import logging
import signal
from typing import NoReturn
from uuid import uuid4

from devmind_api.config import get_settings
from devmind_api.db import MongoManager
from devmind_api.logging import configure_logging
from devmind_worker.jobs import JobRepository

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.worker_enabled:
        logger.info("Worker is disabled by WORKER_ENABLED=false")
        return

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signame in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(signal, signame), stop_event.set)
        except NotImplementedError:
            pass

    manager = MongoManager(settings)
    await manager.connect()
    repository = JobRepository(manager.database)
    worker_id = f"devmind-worker-{uuid4()}"
    try:
        while not stop_event.is_set():
            lease = await repository.claim_next(worker_id)
            if lease is None:
                await asyncio.sleep(2)
                continue
            await repository.complete(lease.job_id)
    finally:
        await manager.close()


def main() -> NoReturn:
    asyncio.run(run_worker())
    raise SystemExit(0)


if __name__ == "__main__":
    main()
