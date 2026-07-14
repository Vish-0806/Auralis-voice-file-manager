"""User Preference Service public interface module."""

import logging
from typing import Any, Dict, Optional

from memory.models.domain_models import PreferenceDomain
from memory.preferences.preference_engine import PreferenceEngine
from memory.exceptions import RecordNotFoundError

logger = logging.getLogger(__name__)


class PreferenceService:
    """Sole public gateway/API for all preference operations in Auralis."""

    def __init__(self, engine: Optional[PreferenceEngine] = None) -> None:
        """Initializes the PreferenceService.

        If no engine is provided, instantiates it dynamically using SessionLocal
        and the PreferenceRepository.

        Args:
            engine: Optional custom PreferenceEngine instance.
        """
        if engine is not None:
            self._engine = engine
        else:
            from memory.database.session import SessionLocal
            from memory.repository.preference_repository import PreferenceRepository

            self._db = SessionLocal()
            repository = PreferenceRepository(self._db)
            self._engine = PreferenceEngine(repository)

    def __del__(self) -> None:
        """Ensures the internal database session is closed correctly when garbage collected."""
        if hasattr(self, "_db"):
            try:
                self._db.close()
            except Exception:
                pass

    def create(self, user_id: int, category: str, key: str, value: Any) -> PreferenceDomain:
        """Validates and persists a new preference setting.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key name.
            value: Setting value to create.

        Returns:
            The saved PreferenceDomain object.
        """
        return self._engine.create_preference(user_id, category, key, value)

    def get(self, user_id: int, category: str, key: str) -> Any:
        """Retrieves a preference setting value, falling back to schema default.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key name.

        Returns:
            The preference setting value.
        """
        return self._engine.get_preference(user_id, category, key)

    def update(self, user_id: int, category: str, key: str, value: Any) -> PreferenceDomain:
        """Validates and updates an existing preference setting.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key.
            value: The new setting value.

        Returns:
            The updated PreferenceDomain object.
        """
        return self._engine.update_preference(user_id, category, key, value)

    def set(self, user_id: int, category: str, key: str, value: Any) -> PreferenceDomain:
        """Convenience method to set a preference. Automatically creates or updates it.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key.
            value: The setting value.

        Returns:
            The updated/created PreferenceDomain object.
        """
        try:
            return self._engine.update_preference(user_id, category, key, value)
        except RecordNotFoundError:
            return self._engine.create_preference(user_id, category, key, value)

    def delete(self, user_id: int, category: str, key: str) -> bool:
        """Deletes a user preference setting.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key.

        Returns:
            True if deleted, False if not found.
        """
        return self._engine.delete_preference(user_id, category, key)

    def list(self, user_id: int, category: Optional[str] = None) -> Dict[str, Any]:
        """Lists user preference settings, merged with defaults for missing keys.

        Args:
            user_id: User identifier.
            category: Optional category filter.

        Returns:
            Dictionary containing preferences. If category is given, returns {key: value}.
            Otherwise, returns {category: {key: value}}.
        """
        return self._engine.list_preferences(user_id, category)

    def reset(self, user_id: int, category: Optional[str] = None) -> None:
        """Resets stored user preferences back to schema defaults.

        Args:
            user_id: User identifier.
            category: Optional category to reset.
        """
        self._engine.reset_preferences(user_id, category)
