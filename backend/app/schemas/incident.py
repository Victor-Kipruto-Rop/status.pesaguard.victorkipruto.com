from datetime import datetime, timezone

from pydantic import BaseModel

from app.models.incident import IncidentSeverity, IncidentUpdateStatus


class IncidentUpdateOut(BaseModel):
    """Matches the {timestamp, status, description} shape js/incidents.js reads
    for `incident.timeline`."""

    timestamp: datetime
    status: IncidentUpdateStatus
    description: str

    @classmethod
    def from_update(cls, update) -> "IncidentUpdateOut":
        return cls(timestamp=update.created_at, status=update.status, description=update.description)


class IncidentSummaryOut(BaseModel):
    """
    The compact shape used in status.json's `activeIncidents` list, and by
    the recent-incidents section on the home page.
    """

    id: str
    title: str
    status: IncidentUpdateStatus
    severity: IncidentSeverity
    created: datetime
    resolved: datetime | None = None

    @classmethod
    def from_incident(cls, incident) -> "IncidentSummaryOut":
        return cls(
            id=incident.id,
            title=incident.title,
            status=incident.current_status,
            severity=incident.severity,
            created=incident.created_at,
            resolved=incident.resolved_at,
        )


class IncidentOut(IncidentSummaryOut):
    """Full incident, including timeline and affected services — matches what
    js/incidents.js expects for `renderIncidentDetail` / `renderIncidentCard`."""

    duration: str | None = None
    services: list[str] = []
    timeline: list[IncidentUpdateOut] = []

    @classmethod
    def from_incident(cls, incident) -> "IncidentOut":
        summary = IncidentSummaryOut.from_incident(incident)
        return cls(
            **summary.model_dump(),
            duration=_format_duration(incident.created_at, incident.resolved_at),
            services=(incident.affected_service_slugs or "").split(",") if incident.affected_service_slugs else [],
            timeline=[IncidentUpdateOut.from_update(u) for u in incident.updates],
        )


class IncidentCreate(BaseModel):
    title: str
    severity: IncidentSeverity
    affected_service_slugs: list[str] = []
    initial_status: IncidentUpdateStatus = IncidentUpdateStatus.investigating
    initial_description: str


class IncidentUpdateCreate(BaseModel):
    status: IncidentUpdateStatus
    description: str


def _format_duration(start: datetime, end: datetime | None) -> str | None:
    if end is None:
        return None
    # Normalize to aware UTC before subtracting: depending on the DB backend
    # (SQLite in dev/tests vs Postgres in production), a server_default
    # timestamp can come back naive while a Python-assigned one stays aware.
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    delta = end - start
    total_minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours == 0:
        return f"{minutes}m"
    return f"{hours}h {minutes}m"
