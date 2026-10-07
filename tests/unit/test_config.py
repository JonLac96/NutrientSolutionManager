import pytest
from app.core.config import Settings, get_settings


def test_settings_defaults_and_environment_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "NSM_DATABASE_URL",
        "NSM_LOG_LEVEL",
        "NSM_DEFAULT_STABILIZATION_SECONDS",
        "NSM_DEFAULT_MAX_CORRECTION_ATTEMPTS",
        "NSM_DEFAULT_MAX_CYCLE_DURATION_MINUTES",
    ):
        monkeypatch.delenv(name, raising=False)

    defaults = Settings(_env_file=None)
    assert defaults.database_url == "sqlite:///./nsm.db"
    assert defaults.log_level == "INFO"
    assert defaults.default_stabilization_seconds == 120
    assert defaults.default_max_correction_attempts == 3
    assert defaults.default_max_cycle_duration_minutes == 1440

    monkeypatch.setenv("NSM_DATABASE_URL", "sqlite:///./override.db")
    monkeypatch.setenv("NSM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NSM_DEFAULT_STABILIZATION_SECONDS", "15")
    monkeypatch.setenv("NSM_DEFAULT_MAX_CORRECTION_ATTEMPTS", "9")
    monkeypatch.setenv("NSM_DEFAULT_MAX_CYCLE_DURATION_MINUTES", "60")
    get_settings.cache_clear()
    overridden = get_settings()
    assert overridden.database_url == "sqlite:///./override.db"
    assert overridden.log_level == "DEBUG"
    assert overridden.default_stabilization_seconds == 15
    assert overridden.default_max_correction_attempts == 9
    assert overridden.default_max_cycle_duration_minutes == 60
