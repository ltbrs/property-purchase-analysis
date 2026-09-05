from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    database_url = get_settings().database_url
    if database_url is None:
        raise RuntimeError("DATABASE_URL is not configured")

    url = make_url(database_url)
    connect_args: dict[str, object] = {}
    if url.get_backend_name() == "postgresql" and url.port == 6543:
        # Supabase transaction pooling does not support named prepared statements.
        connect_args["prepare_threshold"] = None

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args,
    )


def get_db_session() -> Generator[Session]:
    try:
        engine = get_engine()
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from error

    with Session(engine) as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_db_session)]
