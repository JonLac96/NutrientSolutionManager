from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """Speichert naiv in UTC, liefert zeitzonenbehaftet in UTC zurück."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naives datetime ist nicht erlaubt.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)
