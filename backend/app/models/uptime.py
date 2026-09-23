import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class UptimeDailyRecord(Base):
    """
    One row per (component, day). Populated by the worker's nightly
    aggregation job from raw health-check results.
    """

    __tablename__ = "uptime_daily_records"
    __table_args__ = (UniqueConstraint("component_id", "day", name="uq_component_day"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)

    # Percentage of successful checks that day, 0-100. Null if no checks ran.
    uptime_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    downtime_minutes: Mapped[float] = mapped_column(Float, default=0)
