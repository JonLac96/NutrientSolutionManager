import logging
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.core.time import set_clock
from app.main import create_app
from fastapi.testclient import TestClient
from tests.support import PROJECT_ROOT, point_database


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def test_startup_migrates_empty_database_and_reports_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    point_database(monkeypatch, tmp_path / "fresh.db")
    moment = datetime(2026, 10, 7, 18, 0, tzinfo=timezone.utc)
    set_clock(lambda: moment)
    application = create_app()
    with caplog.at_level(logging.INFO):
        with TestClient(application) as client:
            health = client.get("/health")
            version = client.get("/version")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert "Systemzeit: 2026-10-07T18:00:00+00:00" in caplog.text

    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        expected_version = tomllib.load(handle)["project"]["version"]
    body = version.json()
    assert version.status_code == 200
    assert body["version"] == expected_version
    assert body["alembic_revision"] == "a1c0e5d8b347"
    assert _parse_utc(body["started_at"]) == moment


def test_failed_migration_prevents_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail() -> None:
        raise RuntimeError("migration failed")

    monkeypatch.setattr("app.main.upgrade_database", fail)
    application = create_app()
    with pytest.raises(RuntimeError, match="migration failed"):
        with TestClient(application):
            pass


def test_health_fails_when_database_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("file", encoding="utf-8")
    point_database(monkeypatch, blocked / "nsm.db")
    application = create_app(migrate=False)
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/health")
    assert response.status_code != 200
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Unerwarteter Fehler.",
            "details": None,
        }
    }
