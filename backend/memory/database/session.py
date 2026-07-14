"""Database session management module for Auralis.

Provides local database session makers and context generator utilities
compatible with FastAPI dependency injection lifecycles.
"""

import logging
from typing import Generator
from sqlalchemy.orm import sessionmaker, Session
from memory.database.database import get_engine

logger = logging.getLogger(__name__)

# Configures local session class bound to singleton database engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_engine(),
    expire_on_commit=False,
    future=True,  # Enforces SQLAlchemy 2.x standards
)


def get_db() -> Generator[Session, None, None]:
    """Generates database sessions with lifecycle cleanup.

    Designed for use with FastAPI dependency injection (`Depends`).
    Automatically rolls back transactions in the event of an unhandled exception
    and ensures the session is closed.

    Yields:
        Session: Active database session.
    """
    logger.debug("Opening new database session.")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(
            "Transaction rollback initiated due to exception in database session context",
            exc_info=True,
        )
        db.rollback()
        raise e
    finally:
        logger.debug("Closing database session.")
        db.close()
