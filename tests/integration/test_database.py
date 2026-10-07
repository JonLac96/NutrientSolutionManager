from pathlib import Path

import pytest
from app.core.database import create_db_engine
from app.core.migrate import current_revision
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from tests.support import point_database


def test_foreign_key_violation_raises(engine: Engine) -> None:
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1

    metadata = MetaData()
    Table("parents", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "children",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parents.id"), nullable=False),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(child.insert().values(id=1, parent_id=999))


def test_file_engine_sets_sqlite_pragmas(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    point_database(monkeypatch, tmp_path / "pragmas.db")
    engine = create_db_engine()
    try:
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
            assert current_revision(connection) is None
            assert inspect(connection).get_table_names() == []
    finally:
        engine.dispose()
