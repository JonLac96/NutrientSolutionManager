from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from tests.support import create_test_engine, project_db_snapshot


def test_tests_do_not_touch_project_database(
    client: TestClient,
    session: Session,
) -> None:
    before = project_db_snapshot()
    assert client.get("/health").status_code == 200
    assert session.execute(text("SELECT 1")).scalar_one() == 1
    assert project_db_snapshot() == before


def test_two_engines_do_not_share_a_database() -> None:
    first = create_test_engine()
    second = create_test_engine()
    try:
        with first.begin() as connection:
            connection.execute(text("CREATE TABLE only_here (id INTEGER PRIMARY KEY)"))
        with second.connect() as connection:
            names = connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'table'"),
            ).scalars()
            assert "only_here" not in set(names)
    finally:
        first.dispose()
        second.dispose()


def test_fixture_engines_are_independent(engine: Engine) -> None:
    with engine.connect() as connection:
        names = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table'"),
        ).scalars()
        assert "only_here" not in set(names)
