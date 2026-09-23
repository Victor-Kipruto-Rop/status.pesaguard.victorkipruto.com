from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.uptime import UptimeResponse
from app.services.uptime_service import UptimeService

router = APIRouter(tags=["uptime"])


@router.get("/uptime", response_model=UptimeResponse)
async def get_uptime(
    days: int = Query(90, ge=1, le=365, description="Lookback window in days"),
    db: AsyncSession = Depends(get_db),
):
    return await UptimeService(db).get_uptime(days=days)
