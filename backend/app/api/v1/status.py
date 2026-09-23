from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.status import StatusResponse
from app.services.status_service import StatusService

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status(
    use_cache: bool = Query(True, description="Set false to bypass the Redis cache (debugging only)."),
    db: AsyncSession = Depends(get_db),
):
    service = StatusService(db)
    return await service.get_status(use_cache=use_cache)
