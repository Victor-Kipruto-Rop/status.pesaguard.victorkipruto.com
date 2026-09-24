"""
Standalone worker process: polls the real PesaGuard API's /health on a
fixed interval and updates this status page's component records.

Run with:  python -m worker.main
(the docker-compose "worker" service does exactly this)
"""
import asyncio
import logging

from app.config import get_settings
from app.database.session import AsyncSessionLocal
from app.monitoring.checker import HealthChecker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pesaguard_status.worker")

settings = get_settings()


async def run_forever() -> None:
    logger.info(
        "Starting health-check worker: polling %s%s every %ss",
        settings.pesaguard_api_base_url,
        settings.pesaguard_api_health_path,
        settings.monitor_poll_interval_seconds,
    )
    while True:
        async with AsyncSessionLocal() as session:
            checker = HealthChecker(session)
            try:
                result = await checker.check_once()
                if result.get("reachable"):
                    logger.info("Poll ok — statuses: %s", result.get("statuses"))
                else:
                    logger.warning("Poll failed — marking components unreachable: %s", result.get("error"))
            except Exception:
                logger.exception("Unexpected error during health-check poll")
            finally:
                await checker.close()
        await asyncio.sleep(settings.monitor_poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_forever())
