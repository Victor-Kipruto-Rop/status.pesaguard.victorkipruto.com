from datetime import datetime

from pydantic import BaseModel

from app.schemas.component import ComponentOut
from app.schemas.incident import IncidentSummaryOut
from app.schemas.maintenance import MaintenanceSummaryOut


class OverallStatus(BaseModel):
    status: str
    label: str
    description: str


class StatusResponse(BaseModel):
    """Mirrors frontend/data/status.json exactly — see js/status.js."""

    version: str = "1.0.0"
    generatedAt: datetime | None = None
    dataSource: str = "pesaguard-status-api"
    verified: bool = True
    note: str | None = None
    lastUpdated: datetime | None = None
    overall: OverallStatus
    services: list[ComponentOut]
    activeIncidents: list[IncidentSummaryOut]
    activeMaintenance: list[MaintenanceSummaryOut]
