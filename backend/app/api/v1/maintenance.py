from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.maintenance import MaintenanceStatus
from app.schemas.maintenance import MaintenanceCreate, MaintenanceOut, MaintenanceSummaryOut
from app.services.maintenance_service import MaintenanceService
from app.services.status_service import StatusService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("", response_model=list[MaintenanceOut])
async def list_maintenance(db: AsyncSession = Depends(get_db)):
    return await MaintenanceService(db).list_all()


@router.get("/active", response_model=list[MaintenanceSummaryOut])
async def list_active_maintenance(db: AsyncSession = Depends(get_db)):
    return await MaintenanceService(db).list_active_or_upcoming()


@router.post("", response_model=MaintenanceOut, status_code=201)
async def create_maintenance(data: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    created = await MaintenanceService(db).create(data)
    await StatusService(db).invalidate_cache()
    return created


@router.patch("/{maintenance_id}/status", response_model=MaintenanceOut)
async def update_maintenance_status(maintenance_id: str, status: MaintenanceStatus, db: AsyncSession = Depends(get_db)):
    updated = await MaintenanceService(db).update_status(maintenance_id, status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Maintenance window not found")
    await StatusService(db).invalidate_cache()
    return updated
