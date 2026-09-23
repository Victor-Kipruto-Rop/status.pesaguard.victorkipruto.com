from fastapi import APIRouter

from app.api.v1 import components, health, incidents, maintenance, status, subscriptions, uptime

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(status.router)
api_router.include_router(components.router)
api_router.include_router(incidents.router)
api_router.include_router(maintenance.router)
api_router.include_router(uptime.router)
api_router.include_router(subscriptions.router)
