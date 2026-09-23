from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.component import ComponentCreate, ComponentOut, ComponentStatusUpdate
from app.services.component_service import ComponentService
from app.services.status_service import StatusService

router = APIRouter(prefix="/components", tags=["components"])


@router.get("", response_model=list[ComponentOut])
async def list_components(db: AsyncSession = Depends(get_db)):
    return await ComponentService(db).list_components()


@router.post("", response_model=ComponentOut, status_code=201)
async def create_component(data: ComponentCreate, db: AsyncSession = Depends(get_db)):
    created = await ComponentService(db).create_component(data)
    await StatusService(db).invalidate_cache()
    return created


@router.patch("/{slug}/status", response_model=ComponentOut)
async def update_component_status(slug: str, data: ComponentStatusUpdate, db: AsyncSession = Depends(get_db)):
    """
    Called by the health-checker/monitoring worker whenever a probe result
    changes a component's status. Also used to invalidate the cached
    aggregate status response so the next page load reflects it immediately.
    """
    updated = await ComponentService(db).update_status(slug, data.status, data.latency_ms)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Component '{slug}' not found")
    await StatusService(db).invalidate_cache()
    return updated
