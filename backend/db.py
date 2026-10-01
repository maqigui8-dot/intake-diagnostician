import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


EXPECTED_DATABASE_REVISION = "20260917_03"


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> Engine:
    options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)


DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = build_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = (
    sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    if engine is not None
    else None
)


def configure_database(database_url: str) -> None:
    global DATABASE_URL, engine, SessionLocal
    DATABASE_URL = database_url
    engine = build_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


@contextmanager
def get_database_session():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is required")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database() -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


def check_database_revision(database_engine: Engine | None = None) -> bool:
    target_engine = database_engine or engine
    if target_engine is None:
        return False
    try:
        with target_engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except Exception:
        return False
    return revision == EXPECTED_DATABASE_REVISION
