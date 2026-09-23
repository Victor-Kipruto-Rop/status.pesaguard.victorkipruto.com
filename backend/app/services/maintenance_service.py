from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance, MaintenanceStatus
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.maintenance import MaintenanceCreate, MaintenanceOut, MaintenanceSummaryOut


class MaintenanceService:
    def __init__(self, session: AsyncSession):
        self.repo = MaintenanceRepository(session)

    async def list_all(self) -> list[MaintenanceOut]:
        items = await self.repo.list_all()
        return [MaintenanceOut.from_maintenance(m) for m in items]

    async def list_active_or_upcoming(self) -> list[MaintenanceSummaryOut]:
        items = await self.repo.list_active_or_upcoming()
        return [MaintenanceSummaryOut.from_maintenance(m) for m in items]

    async def create(self, data: MaintenanceCreate) -> MaintenanceOut:
        maintenance = Maintenance(
            title=data.title,
            description=data.description,
            affected_service_slugs=",".join(data.affected_service_slugs) or None,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            status=MaintenanceStatus.scheduled,
        )
        created = await self.repo.create(maintenance)
        return MaintenanceOut.from_maintenance(created)

    async def update_status(self, maintenance_id: str, status: MaintenanceStatus) -> MaintenanceOut | None:
        maintenance = await self.repo.get_by_id(maintenance_id)
        if maintenance is None:
            return None
        updated = await self.repo.update_status(maintenance, status)
        return MaintenanceOut.from_maintenance(updated)
