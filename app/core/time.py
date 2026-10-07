from collections.abc import Callable
from datetime import datetime, timezone

_Clock = Callable[[], datetime]


def _system_clock() -> datetime:
    return datetime.now(timezone.utc)


_clock: _Clock = _system_clock


def utcnow() -> datetime:
    return _clock()


def set_clock(clock: _Clock) -> None:
    global _clock
    _clock = clock


def reset_clock() -> None:
    global _clock
    _clock = _system_clock
