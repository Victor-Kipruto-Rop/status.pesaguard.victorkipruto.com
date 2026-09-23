from datetime import datetime

from pydantic import BaseModel

from app.models.maintenance import MaintenanceStatus


class MaintenanceSummaryOut(BaseModel):
    id: str
    title: str
    status: MaintenanceStatus
    scheduled_start: datetime
    scheduled_end: datetime

    @classmethod
    def from_maintenance(cls, m) -> "MaintenanceSummaryOut":
        return cls(
            id=m.id,
            title=m.title,
            status=m.status,
            scheduled_start=m.scheduled_start,
            scheduled_end=m.scheduled_end,
        )


class MaintenanceOut(MaintenanceSummaryOut):
    description: str | None = None
    services: list[str] = []

    @classmethod
    def from_maintenance(cls, m) -> "MaintenanceOut":
        summary = MaintenanceSummaryOut.from_maintenance(m)
        return cls(
            **summary.model_dump(),
            description=m.description,
            services=(m.affected_service_slugs or "").split(",") if m.affected_service_slugs else [],
        )


class MaintenanceCreate(BaseModel):
    title: str
    description: str | None = None
    affected_service_slugs: list[str] = []
    scheduled_start: datetime
    scheduled_end: datetime
