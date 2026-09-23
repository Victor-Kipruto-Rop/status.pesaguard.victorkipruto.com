from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.incident import IncidentCreate, IncidentOut, IncidentSummaryOut, IncidentUpdateCreate
from app.services.incident_service import IncidentService
from app.services.status_service import StatusService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    return await IncidentService(db).list_all()


@router.get("/active", response_model=list[IncidentSummaryOut])
async def list_active_incidents(db: AsyncSession = Depends(get_db)):
    return await IncidentService(db).list_active()


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    incident = await IncidentService(db).get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentOut, status_code=201)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    created = await IncidentService(db).create(data)
    await StatusService(db).invalidate_cache()
    return created


@router.post("/{incident_id}/updates", response_model=IncidentOut)
async def add_incident_update(incident_id: str, data: IncidentUpdateCreate, db: AsyncSession = Depends(get_db)):
    updated = await IncidentService(db).add_update(incident_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    await StatusService(db).invalidate_cache()
    return updated
