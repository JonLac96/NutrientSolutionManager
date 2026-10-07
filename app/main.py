import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from importlib.metadata import version
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.database import create_session_factory, get_session
from app.core.migrate import current_revision, upgrade_database
from app.core.time import utcnow
from app.jobs.recovery import recover_interrupted_jobs
from app.schemas.system import HealthResponse, VersionResponse

logger = logging.getLogger(__name__)

_PACKAGE_NAME = "nutrient-solution-manager"
SessionDep = Annotated[Session, Depends(get_session)]


def application_version() -> str:
    return version(_PACKAGE_NAME)


def configure_logging(level: str) -> None:
    resolved = level.upper()
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger().setLevel(resolved)


def create_app(*, migrate: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings = get_settings()
        configure_logging(settings.log_level)
        started_at = utcnow()
        app.state.started_at = started_at
        logger.info("Anwendung startet. Systemzeit: %s", started_at.isoformat())
        if migrate:
            upgrade_database()
        engine, session_factory = create_session_factory(settings.database_url)
        app.state.session_factory = session_factory
        try:
            recover_interrupted_jobs()
            logger.info("Anwendung nimmt Anfragen an.")
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Nutrient Solution Manager",
        version=application_version(),
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    @app.get("/health", response_model=HealthResponse)
    def health(session: SessionDep) -> HealthResponse:
        session.execute(text("SELECT 1")).scalar_one()
        return HealthResponse(status="ok")

    @app.get("/version", response_model=VersionResponse)
    def version_info(request: Request, session: SessionDep) -> VersionResponse:
        started_at: datetime = request.app.state.started_at
        return VersionResponse(
            version=application_version(),
            alembic_revision=current_revision(session.connection()),
            started_at=started_at,
        )

    return app


app = create_app()
