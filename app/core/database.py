from collections.abc import Generator
from typing import Any, cast

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def set_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_db_engine(database_url: str | None = None) -> Engine:
    url = get_settings().database_url if database_url is None else database_url
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", set_sqlite_pragmas)
    return engine


def create_session_factory(
    database_url: str | None = None,
) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_db_engine(database_url)
    return engine, sessionmaker(bind=engine)


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory = cast(sessionmaker[Session], request.app.state.session_factory)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
