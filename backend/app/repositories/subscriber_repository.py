from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber


class SubscriberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Subscriber | None:
        result = await self.session.execute(select(Subscriber).where(Subscriber.email == email))
        return result.scalar_one_or_none()

    async def create(self, subscriber: Subscriber) -> Subscriber:
        self.session.add(subscriber)
        await self.session.commit()
        await self.session.refresh(subscriber)
        return subscriber

    async def get_by_unsubscribe_token(self, token: str) -> Subscriber | None:
        result = await self.session.execute(select(Subscriber).where(Subscriber.unsubscribe_token == token))
        return result.scalar_one_or_none()

    async def delete(self, subscriber: Subscriber) -> None:
        await self.session.delete(subscriber)
        await self.session.commit()
