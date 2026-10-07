from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    version: str
    alembic_revision: str | None
    started_at: datetime
