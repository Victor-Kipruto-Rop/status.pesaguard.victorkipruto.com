from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.component import Component


class ComponentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Component]:
        result = await self.session.execute(select(Component).order_by(Component.display_order, Component.name))
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Component | None:
        result = await self.session.execute(select(Component).where(Component.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_id(self, component_id: str) -> Component | None:
        return await self.session.get(Component, component_id)

    async def create(self, component: Component) -> Component:
        self.session.add(component)
        await self.session.commit()
        await self.session.refresh(component)
        return component

    async def update_status(self, component: Component, status, latency_ms: float | None) -> Component:
        component.status = status
        if latency_ms is not None:
            component.latency_ms = latency_ms
        await self.session.commit()
        await self.session.refresh(component)
        return component
