from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.uptime import UptimeDailyRecord


class UptimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_component(self, component_id: str, days: int) -> list[UptimeDailyRecord]:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(UptimeDailyRecord)
            .where(UptimeDailyRecord.component_id == component_id, UptimeDailyRecord.day >= since)
            .order_by(UptimeDailyRecord.day.asc())
        )
        return list(result.scalars().all())

    async def list_all_recent(self, days: int) -> list[UptimeDailyRecord]:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(UptimeDailyRecord).where(UptimeDailyRecord.day >= since).order_by(UptimeDailyRecord.day.asc())
        )
        return list(result.scalars().all())

    async def upsert_day(self, component_id: str, day: date, uptime_pct: float, status: str, downtime_minutes: float) -> UptimeDailyRecord:
        result = await self.session.execute(
            select(UptimeDailyRecord).where(
                UptimeDailyRecord.component_id == component_id, UptimeDailyRecord.day == day
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = UptimeDailyRecord(component_id=component_id, day=day)
            self.session.add(record)
        record.uptime_pct = uptime_pct
        record.status = status
        record.downtime_minutes = downtime_minutes
        await self.session.commit()
        await self.session.refresh(record)
        return record
