from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.time import utcnow
from app.core.types import UtcDateTime


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
