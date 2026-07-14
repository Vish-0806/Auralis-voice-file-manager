"""User Preference Validator class."""

from typing import Any
from memory.preferences.preference_models import VALID_PREFERENCES, InvalidPreferenceError


class PreferenceValidator:
    """Validator for user preferences verifying category, key, type, and required fields."""

    @staticmethod
    def validate(category: str, key: str, value: Any) -> None:
        """Validates a preference key-value pair against the configuration schema.

        Args:
            category: The preference category (e.g. 'ide', 'theme').
            key: The preference setting name.
            value: The preference setting value.

        Raises:
            InvalidPreferenceError: If the category, key, or value type fails validation.
        """
        category_lower = category.lower()
        if category_lower not in VALID_PREFERENCES:
            raise InvalidPreferenceError(
                f"Invalid preference category: '{category}'. Allowed categories: {list(VALID_PREFERENCES.keys())}"
            )

        key_schemas = VALID_PREFERENCES[category_lower]
        if key not in key_schemas:
            raise InvalidPreferenceError(
                f"Invalid key '{key}' under category '{category}'. Allowed keys: {list(key_schemas.keys())}"
            )

        schema = key_schemas[key]
        expected_type = schema.value_type

        # Forgiving validation: Allow int for float types
        if expected_type is float and isinstance(value, int):
            return

        # Special check for bool since isinstance(True, int) is True in Python
        if expected_type is bool and not isinstance(value, bool):
            raise InvalidPreferenceError(
                f"Invalid type for '{category}.{key}'. Expected {expected_type.__name__}, got {type(value).__name__}."
            )

        # General type check
        if expected_type is not bool and not isinstance(value, expected_type):
            raise InvalidPreferenceError(
                f"Invalid type for '{category}.{key}'. Expected {expected_type.__name__}, got {type(value).__name__}."
            )

    @staticmethod
    def get_defaults(category: str) -> dict[str, Any]:
        """Retrieves default settings for a given category.

        Args:
            category: The preference category.

        Returns:
            Dictionary containing key-value defaults for the category.

        Raises:
            InvalidPreferenceError: If the category is invalid.
        """
        category_lower = category.lower()
        if category_lower not in VALID_PREFERENCES:
            raise InvalidPreferenceError(f"Invalid preference category: '{category}'")

        defaults = {}
        for key, schema in VALID_PREFERENCES[category_lower].items():
            if schema.default is not None:
                defaults[key] = schema.default
        return defaults
