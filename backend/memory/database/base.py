"""Database declarative base module for Auralis.

Provides the base class for declarative ORM models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base class for all SQLAlchemy ORM models.

    Enforces PEP 484 type annotations and serves as the registry for
    database schemas and metadata.
    """

    pass
