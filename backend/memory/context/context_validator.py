"""User Context Validator class."""

from typing import Any
from memory.context.context_models import ContextType, InvalidContextError


class ContextValidator:
    """Validates user context properties, types, and schema requirements."""

    @staticmethod
    def validate(context_type: str, value: Any) -> None:
        """Checks if a context type and value conform to requirements.

        Args:
            context_type: The context type name.
            value: Context value payload.

        Raises:
            InvalidContextError: If the type or value format fails validation.
        """
        # 1. Validate Context Type
        try:
            enum_type = ContextType(context_type)
        except ValueError:
            allowed = [c.value for c in ContextType]
            raise InvalidContextError(
                f"Invalid context type: '{context_type}'. Allowed types: {allowed}"
            )

        # 2. Validate Type-Specific Value Constraints
        if enum_type in [ContextType.RECENT_FILES, ContextType.RECENT_COMMANDS]:
            if not isinstance(value, list):
                raise InvalidContextError(f"Context type '{context_type}' must be a list. Got {type(value).__name__}.")
            for idx, item in enumerate(value):
                if not isinstance(item, str):
                    raise InvalidContextError(
                        f"All items in '{context_type}' list must be strings. Item at index {idx} was {type(item).__name__}."
                    )

        elif enum_type == ContextType.CLIPBOARD:
            if not isinstance(value, (str, dict)):
                raise InvalidContextError(
                    f"Clipboard context must be a string or dict. Got {type(value).__name__}."
                )

        elif enum_type in [ContextType.CURRENT_PROJECT, ContextType.ACTIVE_FOLDER, ContextType.ACTIVE_WORKSPACE]:
            if not isinstance(value, str):
                raise InvalidContextError(
                    f"Workspace/Folder/Project path context must be a string. Got {type(value).__name__}."
                )
