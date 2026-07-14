"""User Preference Engine orchestration business logic."""

import logging
from typing import Any, Dict, Optional

from memory.exceptions import RecordNotFoundError
from memory.models.domain_models import PreferenceDomain
from memory.repository.preference_repository import PreferenceRepository
from memory.preferences.preference_cache import PreferenceCache
from memory.preferences.preference_validator import PreferenceValidator
from memory.preferences.preference_models import (
    VALID_PREFERENCES,
    InvalidPreferenceError,
    DuplicatePreferenceError,
)

logger = logging.getLogger(__name__)


class PreferenceEngine:
    """Orchestrates preferences storage, retrieval, validation, and TTL caching."""

    def __init__(
        self,
        repository: PreferenceRepository,
        cache: Optional[PreferenceCache] = None,
        validator: Optional[PreferenceValidator] = None,
    ) -> None:
        """Initializes PreferenceEngine with dependencies.

        Args:
            repository: User preference database repository.
            cache: Optional custom preference cache.
            validator: Optional custom preference validator.
        """
        self._repository = repository
        self._cache = cache or PreferenceCache()
        self._validator = validator or PreferenceValidator()

    def _get_db_key(self, category: str, key: str) -> str:
        """Constructs a composite database key from category and key."""
        return f"{category.lower()}:{key.lower()}"

    def create_preference(self, user_id: int, category: str, key: str, value: Any) -> PreferenceDomain:
        """Validates, persists, and caches a new preference setting.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key name.
            value: Setting value to create.

        Returns:
            The saved PreferenceDomain object.

        Raises:
            InvalidPreferenceError: If validation fails.
            DuplicatePreferenceError: If the preference setting already exists.
        """
        category_lower = category.lower()
        key_lower = key.lower()
        self._validator.validate(category_lower, key_lower, value)

        db_key = self._get_db_key(category_lower, key_lower)

        # Check for duplicate
        if self._repository.get_by_user_and_key(user_id, db_key) is not None:
            raise DuplicatePreferenceError(
                f"Preference '{category}.{key}' already exists for user {user_id}. Use update instead."
            )

        logger.info(
            "Creating user preference",
            extra={"user_id": user_id, "category": category_lower, "key": key_lower},
        )
        domain = PreferenceDomain(
            user_id=user_id,
            key=db_key,
            value={"value": value},
        )
        saved = self._repository.create(domain)
        self._cache.set(user_id, category_lower, key_lower, value)
        return saved

    def get_preference(self, user_id: int, category: str, key: str) -> Any:
        """Retrieves a preference setting value. Checks cache first, falling back to database or schema defaults.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key name.

        Returns:
            The preference setting value.

        Raises:
            InvalidPreferenceError: If the category or key is invalid.
        """
        category_lower = category.lower()
        key_lower = key.lower()

        # Quick validation of category/key existence
        if category_lower not in VALID_PREFERENCES:
            raise InvalidPreferenceError(f"Invalid preference category: '{category}'")
        if key_lower not in VALID_PREFERENCES[category_lower]:
            raise InvalidPreferenceError(f"Invalid key '{key}' under category '{category}'")

        # Cache check
        cached_val = self._cache.get(user_id, category_lower, key_lower)
        if cached_val is not None:
            logger.debug(
                "Preference cache hit",
                extra={"user_id": user_id, "category": category_lower, "key": key_lower},
            )
            return cached_val

        # Database lookup
        db_key = self._get_db_key(category_lower, key_lower)
        pref = self._repository.get_by_user_and_key(user_id, db_key)
        if pref is not None:
            value = pref.value.get("value")
            self._cache.set(user_id, category_lower, key_lower, value)
            return value

        # Return default value from schema
        schema = VALID_PREFERENCES[category_lower][key_lower]
        logger.debug(
            "Preference database miss; returning schema default",
            extra={"user_id": user_id, "category": category_lower, "key": key_lower},
        )
        return schema.default

    def update_preference(self, user_id: int, category: str, key: str, value: Any) -> PreferenceDomain:
        """Validates, updates, and recaches an existing preference setting.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key.
            value: The new setting value.

        Returns:
            The updated PreferenceDomain object.

        Raises:
            InvalidPreferenceError: If validation fails.
            RecordNotFoundError: If the preference record does not exist.
        """
        category_lower = category.lower()
        key_lower = key.lower()
        self._validator.validate(category_lower, key_lower, value)

        db_key = self._get_db_key(category_lower, key_lower)
        pref = self._repository.get_by_user_and_key(user_id, db_key)
        if pref is None:
            raise RecordNotFoundError(
                f"Preference '{category}.{key}' does not exist for user {user_id}."
            )

        logger.info(
            "Updating user preference",
            extra={"user_id": user_id, "category": category_lower, "key": key_lower},
        )
        pref.value = {"value": value}
        updated = self._repository.update(pref.id, pref)
        if updated is None:
            raise RecordNotFoundError(f"Failed to update preference with ID {pref.id}")

        self._cache.set(user_id, category_lower, key_lower, value)
        return updated

    def delete_preference(self, user_id: int, category: str, key: str) -> bool:
        """Deletes a preference setting, invalidating it from cache.

        Args:
            user_id: User identifier.
            category: Preference category.
            key: Preference key.

        Returns:
            True if deleted, False if not found.
        """
        category_lower = category.lower()
        key_lower = key.lower()
        db_key = self._get_db_key(category_lower, key_lower)

        pref = self._repository.get_by_user_and_key(user_id, db_key)
        if pref is None:
            return False

        logger.info(
            "Deleting user preference",
            extra={"user_id": user_id, "category": category_lower, "key": key_lower},
        )
        result = self._repository.delete(pref.id)
        self._cache.invalidate(user_id, category_lower, key_lower)
        return result

    def list_preferences(self, user_id: int, category: Optional[str] = None) -> Dict[str, Any]:
        """Lists user preference settings, merged with defaults for missing keys.

        Args:
            user_id: User identifier.
            category: Optional category filter.

        Returns:
            Dictionary structure containing preferences. If category is given, returns
            {key: value} for that category. Otherwise, returns {category: {key: value}}.
        """
        category_lower = category.lower() if category else None

        # Build defaults base
        result_dict: Dict[str, Dict[str, Any]] = {}
        if category_lower:
            if category_lower not in VALID_PREFERENCES:
                raise InvalidPreferenceError(f"Invalid preference category: '{category}'")
            result_dict[category_lower] = self._validator.get_defaults(category_lower)
        else:
            for cat in VALID_PREFERENCES:
                result_dict[cat] = self._validator.get_defaults(cat)

        # Retrieve database values
        prefs = self._repository.search({"user_id": user_id})
        for pref in prefs:
            if ":" not in pref.key:
                continue
            cat_part, key_part = pref.key.split(":", 1)
            cat_part = cat_part.lower()
            key_part = key_part.lower()

            if category_lower and cat_part != category_lower:
                continue

            if cat_part in result_dict and key_part in VALID_PREFERENCES[cat_part]:
                result_dict[cat_part][key_part] = pref.value.get("value")

        # Return single category dict if filtered
        if category_lower:
            return result_dict.get(category_lower, {})

        return result_dict

    def reset_preferences(self, user_id: int, category: Optional[str] = None) -> None:
        """Resets stored user preferences back to schema defaults.

        Args:
            user_id: User identifier.
            category: Optional category to reset.
        """
        category_lower = category.lower() if category else None
        prefs = self._repository.search({"user_id": user_id})

        logger.info(
            "Resetting user preferences",
            extra={"user_id": user_id, "category": category_lower},
        )
        for pref in prefs:
            if ":" not in pref.key:
                continue
            cat_part, key_part = pref.key.split(":", 1)
            cat_part = cat_part.lower()
            key_part = key_part.lower()

            if category_lower and cat_part != category_lower:
                continue

            self._repository.delete(pref.id)
            self._cache.invalidate(user_id, cat_part, key_part)

        if not category_lower:
            self._cache.clear(user_id)
