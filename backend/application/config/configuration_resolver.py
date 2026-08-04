"""Configuration Resolver Engine (Phase 14.3.3).

Engine responsible for type-safe value conversions, applying schema default fallbacks,
resolving properties, and generating immutable resolution reports.
"""

from datetime import timedelta
from enum import Enum
import logging
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.application.config.configuration_schema import ConfigurationSchemaManager
from backend.application.config.models import (
    ConfigurationError,
    ConfigurationResolutionResult,
    ResolutionStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationResolver:
    """Production type conversion and configuration resolution engine."""

    def __init__(self, schema_manager: Optional[ConfigurationSchemaManager] = None) -> None:
        """Initialize ConfigurationResolver.

        Args:
            schema_manager: Optional ConfigurationSchemaManager instance.
        """
        self._lock = RLock()
        self._schema_manager = schema_manager or ConfigurationSchemaManager()

        # Metrics
        self._resolution_count: int = 0
        self._conversion_count: int = 0
        self._default_applications: int = 0
        self._type_mismatches: int = 0

    def convert_value(self, value: Any, target_type: Any) -> Any:
        """Convert raw input value to target type.

        Args:
            value: Input value.
            target_type: Target type specification.

        Returns:
            Any: Converted value.

        Raises:
            ValueError or TypeError if conversion fails.
        """
        if value is None or target_type is Any:
            return value

        # If already instance of target type
        if isinstance(target_type, type) and isinstance(value, target_type):
            return value

        # Boolean conversion (case-insensitive boolean string parsing)
        if target_type is bool:
            if isinstance(value, str):
                s = value.strip().lower()
                if s in ("true", "1", "yes", "on"):
                    return True
                elif s in ("false", "0", "no", "off"):
                    return False
                raise ValueError(f"Cannot convert string '{value}' to boolean.")
            return bool(value)

        # Integer conversion
        if target_type is int:
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                return int(value.strip())
            return int(value)

        # Float conversion
        if target_type is float:
            if isinstance(value, str):
                return float(value.strip())
            return float(value)

        # String conversion
        if target_type is str:
            return str(value)

        # Path conversion
        if target_type is Path:
            return Path(str(value))

        # List conversion
        if target_type is list:
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return list(value)

        # Tuple conversion
        if target_type is tuple:
            if isinstance(value, str):
                return tuple(item.strip() for item in value.split(",") if item.strip())
            return tuple(value)

        # Set conversion
        if target_type is set:
            if isinstance(value, str):
                return {item.strip() for item in value.split(",") if item.strip()}
            return set(value)

        # Enum conversion
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            if isinstance(value, target_type):
                return value
            # Match by enum name or value
            for member in target_type:
                if member.name == str(value) or member.value == value:
                    return member
            raise ValueError(f"Value '{value}' is not a valid enum member of {target_type.__name__}.")

        # Timedelta conversion
        if target_type is timedelta:
            if isinstance(value, (int, float)):
                return timedelta(seconds=value)
            if isinstance(value, str):
                return timedelta(seconds=float(value.strip()))

        # Fallback to calling constructor
        if callable(target_type):
            return target_type(value)

        return value

    def resolve_key(self, key: str, raw_value: Any, expected_type: Optional[Any] = None, default: Optional[Any] = None) -> Any:
        """Resolve a single key with type conversion and default fallback.

        Args:
            key: Configuration key string.
            raw_value: Raw input value from sources.
            expected_type: Optional explicit target type.
            default: Optional fallback default.

        Returns:
            Any: Converted/defaulted value.
        """
        with self._lock:
            self._resolution_count += 1
            defn = self._schema_manager.get_definition(key)
            target_type = expected_type or (defn.expected_type if defn else Any)
            fallback_default = default if default is not None else (defn.default_value if defn else None)

            if raw_value is None:
                if fallback_default is not None:
                    self._default_applications += 1
                    return self.convert_value(fallback_default, target_type)
                return None

            try:
                converted = self.convert_value(raw_value, target_type)
                if converted != raw_value:
                    self._conversion_count += 1
                return converted
            except Exception as exc:
                self._type_mismatches += 1
                logger.warning("Failed type conversion for key '%s': %s. Falling back to raw/default.", key, exc)
                return fallback_default if fallback_default is not None else raw_value

    def resolve_all(self, raw_values: Dict[str, Any]) -> ConfigurationResolutionResult:
        """Resolve all properties against registered schemas.

        Args:
            raw_values: Merged dictionary of raw values from sources.

        Returns:
            ConfigurationResolutionResult: Resolution report.
        """
        with self._lock:
            resolved_map: Dict[str, Any] = dict(raw_values)
            converted: List[str] = []
            defaulted: List[str] = []
            missing_required: List[str] = []
            errors: List[ConfigurationError] = []

            for defn in self._schema_manager.get_all_definitions():
                k = defn.key
                if k in raw_values:
                    raw_val = raw_values[k]
                    try:
                        conv_val = self.convert_value(raw_val, defn.expected_type)
                        resolved_map[k] = conv_val
                        if conv_val != raw_val:
                            converted.append(k)
                    except Exception as exc:
                        errors.append(
                            ConfigurationError(
                                key=k,
                                message=f"Type conversion failed for key '{k}': {exc}",
                                error_type="TYPE_CONVERSION_ERROR",
                            )
                        )
                elif defn.default_value is not None:
                    resolved_map[k] = self.convert_value(defn.default_value, defn.expected_type)
                    defaulted.append(k)
                elif defn.required:
                    missing_required.append(k)
                    errors.append(
                        ConfigurationError(
                            key=k,
                            message=f"Required configuration key '{k}' is missing.",
                            error_type="MISSING_REQUIRED_KEY",
                        )
                    )

            return ConfigurationResolutionResult(
                resolved_values=resolved_map,
                converted_keys=tuple(converted),
                defaulted_keys=tuple(defaulted),
                missing_required_keys=tuple(missing_required),
                errors=tuple(errors),
            )

    def statistics(self) -> ResolutionStatistics:
        """Get resolution metrics."""
        with self._lock:
            return ResolutionStatistics(
                resolution_count=self._resolution_count,
                conversion_count=self._conversion_count,
                default_applications=self._default_applications,
                type_mismatches=self._type_mismatches,
            )
