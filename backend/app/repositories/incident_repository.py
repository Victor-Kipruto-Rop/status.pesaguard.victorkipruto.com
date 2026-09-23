from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident import Incident, IncidentUpdate, IncidentUpdateStatus


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Incident]:
        result = await self.session.execute(
            select(Incident).options(selectinload(Incident.updates)).order_by(Incident.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[Incident]:
        result = await self.session.execute(
            select(Incident)
            .options(selectinload(Incident.updates))
            .where(Incident.resolved_at.is_(None))
            .order_by(Incident.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, incident_id: str) -> Incident | None:
        result = await self.session.execute(
            select(Incident).options(selectinload(Incident.updates)).where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def create(self, incident: Incident, first_update: IncidentUpdate) -> Incident:
        # Append via the relationship (not a manual .incident_id assignment)
        # so SQLAlchemy keeps the in-memory `incident.updates` collection in
        # sync — relying on a fresh SELECT after commit to pick up the new
        # row doesn't work reliably once the relationship is already loaded
        # in this session's identity map (expire_on_commit=False).
        incident.updates.append(first_update)
        self.session.add(incident)
        await self.session.commit()
        return incident

    async def add_update(self, incident: Incident, update: IncidentUpdate) -> Incident:
        incident.updates.append(update)
        if update.status == IncidentUpdateStatus.resolved:
            incident.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()
        return incident
