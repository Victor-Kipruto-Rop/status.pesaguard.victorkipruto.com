from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.component_repository import ComponentRepository
from app.repositories.uptime_repository import UptimeRepository
from app.schemas.uptime import DowntimeEntryOut, ServiceUptimeOut, UptimeDayOut, UptimeResponse

# Worse-is-higher ranking, used to pick the "worst" status across components
# for a given day when building the aggregate daily chart.
_STATUS_RANK = {
    "unknown": 0,
    "operational": 1,
    "maintenance": 2,
    "degraded": 3,
    "partial-outage": 4,
    "major-outage": 5,
}


class UptimeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.uptime_repo = UptimeRepository(session)
        self.component_repo = ComponentRepository(session)

    async def get_uptime(self, days: int = 90) -> UptimeResponse:
        components = await self.component_repo.list_all()
        records = await self.uptime_repo.list_all_recent(days=max(days, 90))

        by_component: dict[str, list] = {}
        for r in records:
            by_component.setdefault(r.component_id, []).append(r)

        # --- Per-service summary (90d uptime) ---
        services_out: list[ServiceUptimeOut] = []
        for c in components:
            comp_records = by_component.get(c.id, [])
            pct_values = [r.uptime_pct for r in comp_records if r.uptime_pct is not None]
            uptime90d = round(sum(pct_values) / len(pct_values), 3) if pct_values else None
            services_out.append(
                ServiceUptimeOut(id=c.slug, name=c.name, status=c.status.value, uptime90d=uptime90d)
            )

        # --- Aggregate daily history (worst status + average uptime per day) ---
        by_day: dict[date, list] = {}
        for r in records:
            by_day.setdefault(r.day, []).append(r)

        history: list[UptimeDayOut] = []
        for day in sorted(by_day.keys()):
            day_records = by_day[day]
            pct_values = [r.uptime_pct for r in day_records if r.uptime_pct is not None]
            uptime = round(sum(pct_values) / len(pct_values), 3) if pct_values else None
            worst_status = max((r.status for r in day_records), key=lambda s: _STATUS_RANK.get(s, 0), default="unknown")
            history.append(UptimeDayOut(date=day.isoformat(), status=worst_status, uptime=uptime))

        # Trim to the requested window for the response (records were fetched
        # with a 90-day floor so periods below can always be computed).
        cutoff = date.today() - timedelta(days=days)
        history = [h for h in history if date.fromisoformat(h.date) >= cutoff]

        # --- Rolling periods (1 / 7 / 30 / 90 day averages, across all components) ---
        def period_avg(period_days: int) -> float | None:
            since = date.today() - timedelta(days=period_days)
            values = [r.uptime_pct for r in records if r.day >= since and r.uptime_pct is not None]
            return round(sum(values) / len(values), 3) if values else None

        periods = {
            "24h": period_avg(1),
            "7d": period_avg(7),
            "30d": period_avg(30),
            "90d": period_avg(90),
        }
        overall = periods["90d"]

        # --- Recent downtime entries (component-days with any downtime) ---
        downtime_entries: list[DowntimeEntryOut] = []
        component_by_id = {c.id: c for c in components}
        for r in sorted(records, key=lambda r: r.day, reverse=True):
            if r.downtime_minutes and r.downtime_minutes > 0:
                comp = component_by_id.get(r.component_id)
                if comp is None:
                    continue
                downtime_entries.append(
                    DowntimeEntryOut(
                        service=comp.name,
                        description=f"{comp.name} had reduced availability ({r.status}).",
                        date=r.day,
                        duration=_format_minutes(r.downtime_minutes),
                    )
                )
        downtime_entries = downtime_entries[:10]

        return UptimeResponse(
            overall=overall,
            periods=periods,
            services=services_out,
            history=history,
            recentDowntime=downtime_entries,
        )


def _format_minutes(total_minutes: float) -> str:
    total_minutes = int(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    if hours == 0:
        return f"{minutes}m"
    return f"{hours}h {minutes}m"
