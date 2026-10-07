import subprocess
from pathlib import Path

import pytest

_PROBE = "_architecture_probe.py"


@pytest.mark.parametrize(
    ("directory", "source", "banned"),
    [
        (
            "app/calculations",
            "import sqlalchemy\n\n_used = sqlalchemy.__name__\n",
            True,
        ),
        (
            "app/calculations",
            "from sqlalchemy.orm import Session\n\n_used = Session\n",
            True,
        ),
        (
            "app/calculations",
            "import app.models\n\n_used = app.models.__name__\n",
            True,
        ),
        (
            "app/calculations",
            "from app.models.base import Base\n\n_used = Base\n",
            True,
        ),
        ("app/calculations", "import app.api\n\n_used = app.api.__name__\n", True),
        (
            "app/calculations",
            "import app.services\n\n_used = app.services.__name__\n",
            True,
        ),
        ("app/services", "import fastapi\n\n_used = fastapi.__name__\n", True),
        ("app/services", "import starlette\n\n_used = starlette.__name__\n", True),
        ("app/models", "import app.schemas\n\n_used = app.schemas.__name__\n", True),
        (
            "app/models",
            "from app.schemas.system import HealthResponse\n\n_used = HealthResponse\n",
            True,
        ),
        ("app/models", "import fastapi\n\n_used = fastapi.__name__\n", True),
        ("app/models", "import sqlalchemy\n\n_used = sqlalchemy.__name__\n", False),
        ("app/services", "import app.models\n\n_used = app.models.__name__\n", False),
        ("app/api", "import fastapi\n\n_used = fastapi.__name__\n", False),
    ],
)
def test_layer_import_bans(directory: str, source: str, banned: bool) -> None:
    path = Path(directory) / _PROBE
    path.write_text(source, encoding="utf-8")
    try:
        result = subprocess.run(
            ["ruff", "check", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        path.unlink(missing_ok=True)
    output = result.stdout + result.stderr
    if banned:
        assert result.returncode != 0
        assert "TID251" in output
    else:
        assert result.returncode == 0, output
