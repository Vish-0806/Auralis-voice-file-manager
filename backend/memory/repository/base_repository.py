"""Base repository module for Auralis.

Provides abstract and generic CRUD interfaces mapping domain models
to/from database ORM schemas.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
# pyrefly: ignore [missing-import]
from sqlalchemy import select, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

logger = logging.getLogger(__name__)

TDomain = TypeVar("TDomain", bound=BaseModel)
TORM = TypeVar("TORM")


class BaseRepository(Generic[TDomain, TORM], ABC):
    """Abstract base repository providing database CRUD operations and model mapping.

    Encapsulates all database transaction commits, rollbacks, and queries,
    ensuring SQLAlchemy session contexts do not leak.
    """

    def __init__(self, db: Session, orm_model: Type[TORM]) -> None:
        """Initializes the repository.

        Args:
            db: Active SQLAlchemy Session.
            orm_model: The database ORM model class.
        """
        self.db = db
        self.orm_model = orm_model

    @abstractmethod
    def _to_domain(self, orm: TORM) -> TDomain:
        """Converts an ORM database entity into its Domain representation."""
        pass

    @abstractmethod
    def _to_orm(self, domain: TDomain) -> TORM:
        """Converts a Domain model into its database ORM representation."""
        pass

    def create(self, domain: TDomain) -> TDomain:
        """Saves a new record to the database.

        Args:
            domain: The domain model containing values to insert.

        Returns:
            The saved domain model populated with database values (e.g. autoincrement ID).
        """
        logger.info(
            "Creating database record",
            extra={"orm_model": self.orm_model.__name__},
        )
        orm_obj = self._to_orm(domain)
        try:
            self.db.add(orm_obj)
            self.db.commit()
            self.db.refresh(orm_obj)
            return self._to_domain(orm_obj)
        except Exception as e:
            logger.error(
                "Failed to create database record; rolling back transaction",
                exc_info=True,
                extra={"orm_model": self.orm_model.__name__},
            )
            self.db.rollback()
            raise e

    def get_by_id(self, id: Any) -> Optional[TDomain]:
        """Retrieves a single record by its primary key ID.

        Args:
            id: Primary key value.

        Returns:
            The domain model if found, else None.
        """
        logger.info(
            "Retrieving database record by ID",
            extra={"orm_model": self.orm_model.__name__, "record_id": id},
        )
        orm_obj = self.db.get(self.orm_model, id)
        if orm_obj:
            return self._to_domain(orm_obj)
        return None

    def update(self, id: Any, domain: TDomain) -> Optional[TDomain]:
        """Updates an existing database record.

        Args:
            id: Primary key of the record to update.
            domain: The updated domain model state.

        Returns:
            The updated domain model if successful, else None.
        """
        logger.info(
            "Updating database record",
            extra={"orm_model": self.orm_model.__name__, "record_id": id},
        )
        orm_obj = self.db.get(self.orm_model, id)
        if not orm_obj:
            logger.warning(
                "Record not found for update",
                extra={"orm_model": self.orm_model.__name__, "record_id": id},
            )
            return None

        # Extract domain values excluding auto-generated timestamps/IDs
        domain_dict = domain.model_dump(exclude={"id", "created_at", "updated_at"})
        try:
            for key, value in domain_dict.items():
                if hasattr(orm_obj, key):
                    setattr(orm_obj, key, value)
            self.db.commit()
            self.db.refresh(orm_obj)
            return self._to_domain(orm_obj)
        except Exception as e:
            logger.error(
                "Failed to update database record; rolling back transaction",
                exc_info=True,
                extra={"orm_model": self.orm_model.__name__, "record_id": id},
            )
            self.db.rollback()
            raise e

    def delete(self, id: Any) -> bool:
        """Deletes a database record by primary key.

        Args:
            id: Primary key value.

        Returns:
            True if the record was deleted, False if not found.
        """
        logger.info(
            "Deleting database record",
            extra={"orm_model": self.orm_model.__name__, "record_id": id},
        )
        orm_obj = self.db.get(self.orm_model, id)
        if not orm_obj:
            logger.warning(
                "Record not found for deletion",
                extra={"orm_model": self.orm_model.__name__, "record_id": id},
            )
            return False

        try:
            self.db.delete(orm_obj)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(
                "Failed to delete database record; rolling back transaction",
                exc_info=True,
                extra={"orm_model": self.orm_model.__name__, "record_id": id},
            )
            self.db.rollback()
            raise e

    def list_all(self, limit: int = 100, offset: int = 0) -> List[TDomain]:
        """Lists database records with pagination support.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of domain models.
        """
        logger.info(
            "Listing database records",
            extra={"orm_model": self.orm_model.__name__, "limit": limit, "offset": offset},
        )
        stmt = select(self.orm_model).limit(limit).offset(offset)
        result = self.db.scalars(stmt).all()
        return [self._to_domain(item) for item in result]

    def search(self, filters: dict, limit: int = 100, offset: int = 0) -> List[TDomain]:
        """Searches records using exact keyword filters.

        Args:
            filters: Key-value filters to apply in WHERE clause.
            limit: Maximum records to return.
            offset: Number of records to skip.

        Returns:
            List of domain models matching filter parameters.
        """
        logger.info(
            "Searching database records with filters",
            extra={"orm_model": self.orm_model.__name__, "filters": list(filters.keys())},
        )
        stmt = select(self.orm_model)
        for key, val in filters.items():
            if hasattr(self.orm_model, key):
                stmt = stmt.where(getattr(self.orm_model, key) == val)
        stmt = stmt.limit(limit).offset(offset)
        result = self.db.scalars(stmt).all()
        return [self._to_domain(item) for item in result]

    def exists(self, **kwargs) -> bool:
        """Checks if a record exists matching the filter criteria.

        Args:
            **kwargs: Filter criteria.

        Returns:
            True if a matching record exists, False otherwise.
        """
        logger.info(
            "Checking existence of record",
            extra={"orm_model": self.orm_model.__name__, "criteria": list(kwargs.keys())},
        )
        stmt = select(self.orm_model)
        for key, val in kwargs.items():
            if hasattr(self.orm_model, key):
                stmt = stmt.where(getattr(self.orm_model, key) == val)
        stmt = stmt.limit(1)
        result = self.db.scalars(stmt).first()
        return result is not None

    def count(self, **kwargs) -> int:
        """Counts database records matching the filter criteria.

        Args:
            **kwargs: Filter criteria.

        Returns:
            Count of records matching the filters.
        """
        logger.info(
            "Counting database records",
            extra={"orm_model": self.orm_model.__name__, "criteria": list(kwargs.keys())},
        )
        stmt = select(func.count()).select_from(self.orm_model)
        for key, val in kwargs.items():
            if hasattr(self.orm_model, key):
                stmt = stmt.where(getattr(self.orm_model, key) == val)
        return self.db.scalar(stmt) or 0
