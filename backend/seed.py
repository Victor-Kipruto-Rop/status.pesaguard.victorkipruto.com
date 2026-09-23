"""
Seed the database with the same components the static frontend already
ships in data/status.json, so the API is a drop-in replacement.

Run with:  python seed.py   (inside the backend container/venv)
"""
import asyncio

from app.database.session import AsyncSessionLocal
from app.models.component import Component, ComponentStatus

COMPONENTS = [
    ("api", "API", "REST API for transaction creation, retrieval, and search."),
    ("dashboard", "Dashboard", "Web dashboard for monitoring and managing transactions."),
    ("transactions", "Transactions", "Payment transaction processing."),
    ("reconciliation", "Reconciliation", "Reconciliation of M-Pesa payments against provider records."),
    ("fraud", "Fraud Detection", "Anomaly and fraud signal evaluation."),
    ("webhooks", "Webhooks", "Outbound webhook delivery and retries."),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        for order, (slug, name, description) in enumerate(COMPONENTS):
            existing = await session.execute(select(Component).where(Component.slug == slug))
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                Component(
                    slug=slug,
                    name=name,
                    description=description,
                    status=ComponentStatus.unknown,
                    display_order=order,
                )
            )
        await session.commit()
    print(f"Seeded {len(COMPONENTS)} components (skipping any that already exist).")


if __name__ == "__main__":
    asyncio.run(seed())
