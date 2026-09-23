from datetime import datetime

from pydantic import BaseModel

from app.models.component import ComponentStatus


class ComponentOut(BaseModel):
    """
    NOTE: `id` here is the human-readable slug (e.g. "api"), matching what
    the frontend's data/status.json already used — not the internal UUID
    primary key. Build these with `from_component()`, not `.model_validate()`
    directly, since the field names don't line up 1:1 with the ORM model.
    """

    id: str
    name: str
    description: str | None = None
    status: ComponentStatus
    latency: float | None = None
    uptime: float | None = None
    updated: datetime | None = None

    @classmethod
    def from_component(cls, component) -> "ComponentOut":
        return cls(
            id=component.slug,
            name=component.name,
            description=component.description,
            status=component.status,
            latency=component.latency_ms,
            uptime=component.uptime_pct_90d,
            updated=component.updated_at,
        )


class ComponentCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    display_order: int = 0


class ComponentStatusUpdate(BaseModel):
    """Used by the health-checker / an admin endpoint to push a new reading."""

    status: ComponentStatus
    latency_ms: float | None = None
