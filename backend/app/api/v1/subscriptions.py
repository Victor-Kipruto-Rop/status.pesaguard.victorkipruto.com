from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionOut, status_code=201)
async def subscribe(data: SubscriptionCreate, db: AsyncSession = Depends(get_db)):
    return await SubscriptionService(db).subscribe(data)


@router.delete("/{token}", status_code=204)
async def unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    removed = await SubscriptionService(db).unsubscribe(token)
    if not removed:
        raise HTTPException(status_code=404, detail="Subscription not found")
