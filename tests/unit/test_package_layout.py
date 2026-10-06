import app
import app.api
import app.api.routers
import app.calculations
import app.core
import app.devices
import app.enums
import app.jobs
import app.jobs.types
import app.models
import app.schemas
import app.services


def test_app_package_imports() -> None:
    assert app.__name__ == "app"
