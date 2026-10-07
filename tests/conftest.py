from collections.abc import Iterator
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.core.database import get_session
from app.core.time import reset_clock
from app.main import create_app
from app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from tests.support import create_test_engine, point_database, project_db_snapshot


@pytest.fixture(autouse=True)
def _isolated_runtime() -> Iterator[None]:
    get_settings.cache_clear()
    reset_clock()
    before = project_db_snapshot()
    yield
    assert project_db_snapshot() == before, "Testdatenbank hat nsm.db verändert"
    get_settings.cache_clear()
    reset_clock()


@pytest.fixture
def engine() -> Iterator[Engine]:
    test_engine = create_test_engine()
    Base.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine)
    with factory() as db_session:
        yield db_session


@pytest.fixture
def client(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[TestClient]:
    point_database(monkeypatch, tmp_path / "client.db")
    application = create_app(migrate=False)

    def override_get_session() -> Iterator[Session]:
        yield session

    application.dependency_overrides[get_session] = override_get_session
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
