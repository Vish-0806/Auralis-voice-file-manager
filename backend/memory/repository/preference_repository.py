"""Preference repository module for Auralis."""

import logging
from typing import Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import PreferenceDomain
from memory.orm.preference import Preference
from memory.repository.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PreferenceRepository(BaseRepository[PreferenceDomain, Preference]):
    """Repository mapping Preference domain models to their database ORM schema.

    Exposes specialized query helper methods for preference settings.
    """

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, Preference)

    def _to_domain(self, orm: Preference) -> PreferenceDomain:
        return PreferenceDomain(
            id=orm.id,
            user_id=orm.user_id,
            key=orm.key,
            value=orm.value,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: PreferenceDomain) -> Preference:
        return Preference(
            id=domain.id,
            user_id=domain.user_id,
            key=domain.key,
            value=domain.value,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get_by_user_and_key(self, user_id: int, key: str) -> Optional[PreferenceDomain]:
        """Retrieves a configuration preference value by its owner user_id and key.

        Args:
            user_id: The ID of the owner user.
            key: The configuration setting key string.

        Returns:
            The PreferenceDomain model if found, else None.
        """
        logger.info(
            "Retrieving preference by user and key",
            extra={"user_id": user_id, "key": key},
        )
        stmt = select(Preference).where(
            Preference.user_id == user_id, Preference.key == key
        )
        orm_obj = self.db.scalars(stmt).first()
        if orm_obj:
            return self._to_domain(orm_obj)
        return None

    def get_by_key(self, user_id: int, key: str) -> Optional[PreferenceDomain]:
        """Retrieves a configuration preference value by its owner user_id and key."""
        return self.get_by_user_and_key(user_id, key)
