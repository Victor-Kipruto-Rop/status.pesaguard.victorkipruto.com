from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance, MaintenanceStatus


class MaintenanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Maintenance]:
        result = await self.session.execute(select(Maintenance).order_by(Maintenance.scheduled_start.desc()))
        return list(result.scalars().all())

    async def list_active_or_upcoming(self) -> list[Maintenance]:
        result = await self.session.execute(
            select(Maintenance)
            .where(Maintenance.status.in_([MaintenanceStatus.scheduled, MaintenanceStatus.in_progress]))
            .order_by(Maintenance.scheduled_start.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, maintenance_id: str) -> Maintenance | None:
        return await self.session.get(Maintenance, maintenance_id)

    async def create(self, maintenance: Maintenance) -> Maintenance:
        self.session.add(maintenance)
        await self.session.commit()
        await self.session.refresh(maintenance)
        return maintenance

    async def update_status(self, maintenance: Maintenance, status: MaintenanceStatus) -> Maintenance:
        maintenance.status = status
        await self.session.commit()
        await self.session.refresh(maintenance)
        return maintenance
