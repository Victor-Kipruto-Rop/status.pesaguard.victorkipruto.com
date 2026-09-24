"""
Polls the real PesaGuard API's /health endpoint and updates this status
page's own component records accordingly.

This never writes to, or otherwise touches, api.pesaguard.victorkipruto.com
itself — it only performs a read-only GET against a public health endpoint
that repo already exposes for exactly this purpose.
"""
import logging
import time

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.monitoring.mapper import all_components_unreachable, map_health_payload_to_components
from app.services.component_service import ComponentService
from app.services.status_service import StatusService

logger = logging.getLogger("pesaguard_status.monitoring")

settings = get_settings()


class HealthChecker:
    def __init__(self, session: AsyncSession, client: httpx.AsyncClient | None = None):
        self.session = session
        self.component_service = ComponentService(session)
        self.status_service = StatusService(session)
        # Allow injecting a client (with a mock transport) in tests instead
        # of hitting the real network.
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.monitor_http_timeout_seconds)
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    async def check_once(self) -> dict:
        """
        Runs one poll cycle: fetch /health, map it to component statuses,
        persist them, and invalidate the cached status aggregate. Returns a
        small summary dict, mainly useful for logging/tests.
        """
        url = settings.pesaguard_api_base_url.rstrip("/") + settings.pesaguard_api_health_path
        client = await self._get_client()

        started = time.perf_counter()
        try:
            response = await client.get(url)
            latency_ms = (time.perf_counter() - started) * 1000
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning("Could not reach %s: %s", url, exc)
            statuses = all_components_unreachable()
            await self._apply(statuses, api_latency_ms=None)
            return {"reachable": False, "error": str(exc), "statuses": statuses}

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Non-JSON response from %s (status %s)", url, response.status_code)
            statuses = all_components_unreachable()
            await self._apply(statuses, api_latency_ms=latency_ms)
            return {"reachable": True, "parse_error": True, "statuses": statuses}

        statuses = map_health_payload_to_components(payload)
        await self._apply(statuses, api_latency_ms=latency_ms)
        return {"reachable": True, "payload": payload, "statuses": statuses, "latency_ms": latency_ms}

    async def _apply(self, statuses: dict, api_latency_ms: float | None) -> None:
        for slug, status in statuses.items():
            latency = api_latency_ms if slug == "api" else None
            await self.component_service.update_status(slug, status, latency)
        await self.status_service.invalidate_cache()
