from datetime import datetime, timedelta, timezone

import pytest
from app.core.time import set_clock, utcnow
from app.core.types import UtcDateTime
from app.models import Base
from sqlalchemy.engine import Engine
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Mapped, Session, mapped_column


def test_utc_datetime_roundtrip_and_naive_rejection(
    session: Session, engine: Engine
) -> None:
    column_type = UtcDateTime()
    assert column_type.process_bind_param(None, engine.dialect) is None
    assert column_type.process_result_value(None, engine.dialect) is None

    class UtcProbe(Base):
        __tablename__ = "utc_probes"
        moment: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)

    Base.metadata.create_all(engine, tables=[UtcProbe.__table__])
    try:
        moment = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
        set_clock(lambda: moment)
        row = UtcProbe(moment=moment)
        session.add(row)
        session.commit()
        session.refresh(row)

        assert row.moment == moment
        assert row.moment.tzinfo == timezone.utc
        assert row.created_at == moment
        assert row.updated_at == moment
        assert row.moment <= utcnow()
        assert row.created_at <= utcnow()

        later = moment + timedelta(hours=1)
        set_clock(lambda: later)
        row.moment = datetime(2026, 10, 7, 14, 30, tzinfo=timezone(timedelta(hours=2)))
        session.commit()
        session.refresh(row)
        assert row.moment == datetime(2026, 10, 7, 12, 30, tzinfo=timezone.utc)
        assert row.updated_at == later
        assert row.created_at == moment
        assert row.updated_at <= utcnow()

        naive = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc).replace(tzinfo=None)
        session.add(UtcProbe(moment=naive))
        with pytest.raises(StatementError, match="Naives datetime ist nicht erlaubt."):
            session.commit()
    finally:
        session.rollback()
        Base.metadata.remove(UtcProbe.__table__)
