from pathlib import Path

import pytest
from app.core.exceptions import NotFoundError
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from tests.support import point_database


def _app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FastAPI:
    point_database(monkeypatch, tmp_path / "errors.db")
    return create_app(migrate=False)


def test_not_found_error_uses_error_format(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    application = _app(monkeypatch, tmp_path)

    @application.get("/missing-probe")
    def missing_probe() -> None:
        raise NotFoundError(
            "GrowthStage 42 existiert nicht.",
            code="growth_stage_not_found",
        )

    with TestClient(application) as client:
        response = client.get("/missing-probe")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "growth_stage_not_found",
            "message": "GrowthStage 42 existiert nicht.",
            "details": None,
        }
    }


def test_request_validation_uses_error_format(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    application = _app(monkeypatch, tmp_path)

    class NameBody(BaseModel):
        name: str

    @application.post("/names")
    def create_name(body: NameBody) -> dict[str, str]:
        return {"name": body.name}

    with TestClient(application) as client:
        response = client.post("/names", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Validierung fehlgeschlagen."
    assert "name" in body["error"]["details"]


def test_unhandled_exception_hides_internal_details(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    application = _app(monkeypatch, tmp_path)

    @application.get("/boom")
    def boom() -> None:
        raise RuntimeError("sensible-internal-detail")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Unerwarteter Fehler.",
            "details": None,
        }
    }
    assert "sensible-internal-detail" not in response.text
