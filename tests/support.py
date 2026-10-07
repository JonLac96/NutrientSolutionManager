from pathlib import Path

import pytest
from app.core.config import get_settings
from app.core.database import set_sqlite_pragmas
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DB_NAMES = ("nsm.db", "nsm.db-wal", "nsm.db-shm")


def sqlite_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def point_database(monkeypatch: pytest.MonkeyPatch, path: Path) -> str:
    url = sqlite_url(path)
    monkeypatch.setenv("NSM_DATABASE_URL", url)
    get_settings.cache_clear()
    return url


def project_db_snapshot() -> tuple[bytes | None, ...]:
    snapshots: list[bytes | None] = []
    for name in PROJECT_DB_NAMES:
        path = PROJECT_ROOT / name
        snapshots.append(path.read_bytes() if path.is_file() else None)
    return tuple(snapshots)


def create_test_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", set_sqlite_pragmas)
    return engine
