import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    major = "major"


class IncidentUpdateStatus(str, enum.Enum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"


class Incident(Base):
    """An incident affecting one or more components."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity, name="incident_severity"))

    # Denormalized list of affected component slugs, stored as comma-separated
    # text for simplicity — a join table would be the "correct" normalized
    # form, add one (incident_components) if you need per-component incident
    # history queries.
    affected_service_slugs: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updates: Mapped[list["IncidentUpdate"]] = relationship(
        back_populates="incident", order_by="IncidentUpdate.created_at", cascade="all, delete-orphan"
    )

    @property
    def is_active(self) -> bool:
        return self.resolved_at is None

    @property
    def current_status(self) -> IncidentUpdateStatus:
        if self.updates:
            return self.updates[-1].status
        return IncidentUpdateStatus.investigating


class IncidentUpdate(Base):
    """A single timeline entry on an incident (investigating -> resolved)."""

    __tablename__ = "incident_updates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    status: Mapped[IncidentUpdateStatus] = mapped_column(Enum(IncidentUpdateStatus, name="incident_update_status"))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc))

    incident: Mapped["Incident"] = relationship(back_populates="updates")
