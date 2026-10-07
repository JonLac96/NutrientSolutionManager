from datetime import datetime, timezone

from app.core.time import reset_clock, set_clock, utcnow


def test_set_clock_and_reset() -> None:
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    set_clock(lambda: moment)
    assert utcnow() == moment
    reset_clock()
    current = utcnow()
    assert current.tzinfo is not None
    assert current.utcoffset() == timezone.utc.utcoffset(current)
    assert abs((current - datetime.now(timezone.utc)).total_seconds()) < 2
