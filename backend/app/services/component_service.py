from sqlalchemy.ext.asyncio import AsyncSession

from app.models.component import Component, ComponentStatus
from app.repositories.component_repository import ComponentRepository
from app.schemas.component import ComponentCreate, ComponentOut


class ComponentService:
    def __init__(self, session: AsyncSession):
        self.repo = ComponentRepository(session)

    async def list_components(self) -> list[ComponentOut]:
        components = await self.repo.list_all()
        return [ComponentOut.from_component(c) for c in components]

    async def create_component(self, data: ComponentCreate) -> ComponentOut:
        component = Component(
            slug=data.slug,
            name=data.name,
            description=data.description,
            display_order=data.display_order,
            status=ComponentStatus.unknown,
        )
        created = await self.repo.create(component)
        return ComponentOut.from_component(created)

    async def update_status(self, slug: str, status: ComponentStatus, latency_ms: float | None) -> ComponentOut | None:
        component = await self.repo.get_by_slug(slug)
        if component is None:
            return None
        updated = await self.repo.update_status(component, status, latency_ms)
        return ComponentOut.from_component(updated)
