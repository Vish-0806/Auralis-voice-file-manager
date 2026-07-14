"""SQLAlchemy database engine module.

Instantiates and configures the singleton engine with optimized connection pooling
and SQLAlchemy 2.x standards.
"""

import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from memory.database.config import db_config

logger = logging.getLogger(__name__)

# Global singleton storage for the SQLAlchemy Engine
_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Retrieves or initializes the singleton SQLAlchemy Engine instance.

    Configures connection pooling settings to prevent starvation and ensure
    re-connectivity during system execution.

    Returns:
        The configured Engine instance.
    """
    global _engine
    if _engine is None:
        url = db_config.url
        logger.info(
            "Initializing SQLAlchemy database engine",
            extra={
                "host": db_config.host,
                "port": db_config.port,
                "database_name": db_config.name,
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 1800,
            },
        )
        try:
            _engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
                future=True,  # Enforces SQLAlchemy 2.x standards
            )
            logger.info("SQLAlchemy database engine initialized successfully.")
        except Exception as e:
            logger.critical(
                "Failed to initialize SQLAlchemy database engine",
                exc_info=True,
                extra={"database_url": url},
            )
            raise e

    return _engine
