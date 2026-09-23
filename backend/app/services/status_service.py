from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.cache_service import CacheService
from app.models.component import ComponentStatus
from app.repositories.component_repository import ComponentRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.component import ComponentOut
from app.schemas.incident import IncidentSummaryOut
from app.schemas.maintenance import MaintenanceSummaryOut
from app.schemas.status import OverallStatus, StatusResponse

# Worse-is-higher ranking — the overall banner shows the worst status among
# all components, same logic a human would use to eyeball the page.
_STATUS_RANK = {
    ComponentStatus.unknown: 0,
    ComponentStatus.operational: 1,
    ComponentStatus.maintenance: 2,
    ComponentStatus.degraded: 3,
    ComponentStatus.partial_outage: 4,
    ComponentStatus.major_outage: 5,
}

_OVERALL_COPY = {
    ComponentStatus.operational: ("operational", "All systems operational", "All PesaGuard services are running normally."),
    ComponentStatus.degraded: ("degraded", "Degraded performance", "Some PesaGuard services are experiencing degraded performance."),
    ComponentStatus.partial_outage: ("partial-outage", "Partial outage", "Some PesaGuard services are currently unavailable."),
    ComponentStatus.major_outage: ("major-outage", "Major outage", "PesaGuard is experiencing a major service disruption."),
    ComponentStatus.maintenance: ("maintenance", "Under maintenance", "PesaGuard services are undergoing scheduled maintenance."),
    ComponentStatus.unknown: ("unknown", "Status unavailable", "No monitoring source is connected, so PesaGuard cannot confirm service health."),
}

_CACHE_KEY = "status:v1"


class StatusService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.component_repo = ComponentRepository(session)
        self.incident_repo = IncidentRepository(session)
        self.maintenance_repo = MaintenanceRepository(session)
        self.cache = CacheService()

    async def get_status(self, use_cache: bool = True) -> StatusResponse:
        if use_cache:
            cached = await self.cache.get_json(_CACHE_KEY)
            if cached is not None:
                return StatusResponse.model_validate(cached)

        components = await self.component_repo.list_all()
        active_incidents = await self.incident_repo.list_active()
        active_maintenance = await self.maintenance_repo.list_active_or_upcoming()

        overall_component_status = max(
            (c.status for c in components), key=lambda s: _STATUS_RANK.get(s, 0), default=ComponentStatus.unknown
        )
        status_value, label, description = _OVERALL_COPY[overall_component_status]

        response = StatusResponse(
            generatedAt=datetime.now(timezone.utc),
            verified=any(c.status != ComponentStatus.unknown for c in components),
            note=None if components else "No components have been configured yet.",
            lastUpdated=datetime.now(timezone.utc),
            overall=OverallStatus(status=status_value, label=label, description=description),
            services=[ComponentOut.from_component(c) for c in components],
            activeIncidents=[IncidentSummaryOut.from_incident(i) for i in active_incidents],
            activeMaintenance=[MaintenanceSummaryOut.from_maintenance(m) for m in active_maintenance],
        )

        if use_cache:
            await self.cache.set_json(_CACHE_KEY, response.model_dump(mode="json"))

        return response

    async def invalidate_cache(self) -> None:
        await self.cache.invalidate(_CACHE_KEY)
