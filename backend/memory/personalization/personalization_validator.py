"""Personalization configuration validator."""

from memory.personalization.personalization_models import InvalidPersonalizationConfigError


class PersonalizationValidator:
    """Validates structural properties of user personalization structures."""

    @staticmethod
    def validate_inputs(user_id: int, session_id: str) -> None:
        """Verifies essential inputs are present and typed correctly.

        Args:
            user_id: Owner user ID.
            session_id: Active session ID.

        Raises:
            InvalidPersonalizationConfigError: If constraints fail.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise InvalidPersonalizationConfigError(f"User ID must be a positive integer. Got {user_id}.")

        if not session_id or not isinstance(session_id, str) or not session_id.strip():
            raise InvalidPersonalizationConfigError("Session ID must be a non-empty string.")
