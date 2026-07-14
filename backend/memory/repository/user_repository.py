"""User repository module for Auralis."""

import logging
from typing import Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import UserDomain
from memory.orm.user import User
from memory.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[UserDomain, User]):
    """Repository mapping User domain models to their database ORM schema.

    Exposes specialized query helper methods for user lookups.
    """

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, User)

    def _to_domain(self, orm: User) -> UserDomain:
        return UserDomain(
            id=orm.id,
            username=orm.username,
            email=orm.email,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: UserDomain) -> User:
        return User(
            id=domain.id,
            username=domain.username,
            email=domain.email,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get_by_username(self, username: str) -> Optional[UserDomain]:
        """Retrieves a user by their unique username.

        Args:
            username: The unique username string to find.

        Returns:
            The UserDomain model if found, else None.
        """
        logger.info("Retrieving user by username", extra={"username": username})
        stmt = select(User).where(User.username == username)
        orm_obj = self.db.scalars(stmt).first()
        if orm_obj:
            return self._to_domain(orm_obj)
        return None
