from pathlib import Path

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from app.core.database import create_db_engine
from app.core.migrate import alembic_config, current_revision
from sqlalchemy import inspect
from tests.support import point_database


def test_upgrade_head_and_downgrade_base(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    point_database(monkeypatch, tmp_path / "migrate.db")
    cfg = alembic_config()
    head = ScriptDirectory.from_config(cfg).get_current_head()
    assert head == "a1c0e5d8b347"

    command.upgrade(cfg, "head")
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            assert inspect(connection).get_table_names() == ["alembic_version"]
            assert current_revision(connection) == head
    finally:
        engine.dispose()

    command.downgrade(cfg, "base")
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            assert current_revision(connection) is None
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            assert current_revision(connection) == head
    finally:
        engine.dispose()
