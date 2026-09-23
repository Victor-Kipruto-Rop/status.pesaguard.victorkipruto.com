from datetime import date

from pydantic import BaseModel


class UptimePeriods(BaseModel):
    """Matches status-uptime-summary cards: 24h / 7d / 30d / 90d."""

    day1: float | None = None
    day7: float | None = None
    day30: float | None = None
    day90: float | None = None

    def to_frontend_dict(self) -> dict:
        # Frontend keys are "24h" / "7d" / "30d" / "90d" — not valid Python
        # identifiers, so map them at serialization time instead of using
        # them as field names.
        return {"24h": self.day1, "7d": self.day7, "30d": self.day30, "90d": self.day90}


class ServiceUptimeOut(BaseModel):
    id: str
    name: str
    status: str
    uptime90d: float | None = None


class UptimeDayOut(BaseModel):
    date: str
    status: str
    uptime: float | None = None


class DowntimeEntryOut(BaseModel):
    service: str
    description: str
    date: date
    duration: str


class UptimeResponse(BaseModel):
    """Mirrors frontend/data/uptime.json."""

    version: str = "1.0.0"
    generatedAt: str | None = None
    dataSource: str = "pesaguard-status-api"
    verified: bool = True
    note: str | None = None
    overall: float | None = None
    periods: dict = {}
    services: list[ServiceUptimeOut] = []
    history: list[UptimeDayOut] = []
    recentDowntime: list[DowntimeEntryOut] = []
