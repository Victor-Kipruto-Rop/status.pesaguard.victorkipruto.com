import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentUpdate
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentOut, IncidentSummaryOut, IncidentUpdateCreate


class IncidentService:
    def __init__(self, session: AsyncSession):
        self.repo = IncidentRepository(session)

    async def list_all(self) -> list[IncidentOut]:
        incidents = await self.repo.list_all()
        return [IncidentOut.from_incident(i) for i in incidents]

    async def list_active(self) -> list[IncidentSummaryOut]:
        incidents = await self.repo.list_active()
        return [IncidentSummaryOut.from_incident(i) for i in incidents]

    async def get(self, incident_id: str) -> IncidentOut | None:
        incident = await self.repo.get_by_id(incident_id)
        if incident is None:
            return None
        return IncidentOut.from_incident(incident)

    async def create(self, data: IncidentCreate) -> IncidentOut:
        # Generate the id explicitly rather than relying on the model's
        # default=lambda, which doesn't populate incident.id until flush —
        # too late to link the first IncidentUpdate to it here.
        incident = Incident(
            id=str(uuid.uuid4()),
            title=data.title,
            severity=data.severity,
            affected_service_slugs=",".join(data.affected_service_slugs) or None,
        )
        first_update = IncidentUpdate(
            id=str(uuid.uuid4()), status=data.initial_status, description=data.initial_description
        )
        created = await self.repo.create(incident, first_update)
        return IncidentOut.from_incident(created)

    async def add_update(self, incident_id: str, data: IncidentUpdateCreate) -> IncidentOut | None:
        incident = await self.repo.get_by_id(incident_id)
        if incident is None:
            return None
        update = IncidentUpdate(id=str(uuid.uuid4()), status=data.status, description=data.description)
        updated = await self.repo.add_update(incident, update)
        return IncidentOut.from_incident(updated)
