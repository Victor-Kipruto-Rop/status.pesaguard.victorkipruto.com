import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ComponentStatus(str, enum.Enum):
    operational = "operational"
    degraded = "degraded"
    partial_outage = "partial-outage"
    major_outage = "major-outage"
    maintenance = "maintenance"
    unknown = "unknown"


class Component(Base):
    """A monitored service/component shown on the status page (e.g. API, Dashboard)."""

    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ComponentStatus] = mapped_column(
        Enum(ComponentStatus, name="component_status"), default=ComponentStatus.unknown
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Latest observed values, updated by the monitoring/health-checker.
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    uptime_pct_90d: Mapped[float | None] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(timezone.utc))
