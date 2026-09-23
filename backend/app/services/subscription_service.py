from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.repo = SubscriberRepository(session)

    async def subscribe(self, data: SubscriptionCreate) -> SubscriptionOut:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            return SubscriptionOut.from_subscriber(existing)
        subscriber = Subscriber(email=data.email, confirmed=False)
        created = await self.repo.create(subscriber)
        # TODO: dispatch a confirmation email via notifications/email.py once
        # a real email provider (SES, Postmark, etc.) is wired up.
        return SubscriptionOut.from_subscriber(created)

    async def unsubscribe(self, token: str) -> bool:
        subscriber = await self.repo.get_by_unsubscribe_token(token)
        if subscriber is None:
            return False
        await self.repo.delete(subscriber)
        return True
