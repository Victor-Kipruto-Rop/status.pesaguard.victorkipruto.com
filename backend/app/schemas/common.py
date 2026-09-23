from datetime import datetime

from pydantic import BaseModel


class EnvelopeMeta(BaseModel):
    """
    Every top-level response mirrors the shape of the static data/*.json
    files the frontend already consumes (version, generatedAt, dataSource,
    verified, note) so the existing frontend/js/*.js can point at this API
    with zero changes on the frontend side.
    """

    version: str = "1.0.0"
    generatedAt: datetime | None = None
    dataSource: str = "pesaguard-status-api"
    verified: bool = True
    note: str | None = None
