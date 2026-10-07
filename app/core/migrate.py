from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy.engine import Connection

from app.core.config import get_settings

_ROOT = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    cfg = Config(str(_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    return cfg


def upgrade_database() -> None:
    command.upgrade(alembic_config(), "head")


def current_revision(connection: Connection) -> str | None:
    context = MigrationContext.configure(connection)
    return context.get_current_revision()
