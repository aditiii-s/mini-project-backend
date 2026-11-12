import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

logger = logging.getLogger(__name__)


def _build_engine():
    """Create the SQLAlchemy engine for Supabase PostgreSQL.

    Behind Supabase's transaction pooler (port 6543) PgBouncer hands out a
    different backend connection per transaction, so neither SQLAlchemy's own
    pool nor psycopg's server-side prepared statements can be used.
    """
    kwargs = {"pool_pre_ping": True, "echo": False}

    if settings.uses_transaction_pooler:
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {"prepare_threshold": None}
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 5
        kwargs["pool_recycle"] = 1800

    return create_engine(settings.database_url, **kwargs)


engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency - yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create the tables and enum types. Raises a clear error if unreachable.

    Supabase provisions the `postgres` database itself, so there is no
    CREATE DATABASE step - only the schema objects are created here.
    """
    from app import models  # noqa: F401  (registers the mappers)

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        logger.error("Cannot connect to Supabase at %s", settings.safe_display_url)
        raise RuntimeError(
            "Supabase connection failed. Check DATABASE_URL in backend/.env - copy it "
            "from Project Settings -> Database -> Connection string -> URI and put your "
            "database password in place of [YOUR-PASSWORD].\n"
            f"Tried: {settings.safe_display_url}\nDetails: {exc}"
        ) from exc
