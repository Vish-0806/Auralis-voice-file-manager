"""Configuration Validator Engine (Phase 14.3.3).

Engine responsible for validating resolved configuration values against schema definitions
and constraints, producing detailed error and warning reports.
"""

from datetime import datetime, timezone
import logging
import re
from threading import RLock
from typing import Any, Dict, List, Optional, Pattern , Tuple

from backend.application.config.configuration_schema import ConfigurationSchemaManager
from backend.application.config.interfaces import IConfigurationValidator
from backend.application.config.models import (
    ConfigurationConstraint,
    ConfigurationDefinition,
    ConfigurationError,
    ConfigurationSchema,
    ConfigurationValidationResult,
    ConfigurationWarning,
    ValidationStatistics,
)

logger = logging.getLogger(__name__)


class ConfigurationValidator(IConfigurationValidator):
    """Production configuration validator engine validating values against schema rules and constraints."""

    def __init__(self, schema_manager: Optional[ConfigurationSchemaManager] = None) -> None:
        """Initialize ConfigurationValidator.

        Args:
            schema_manager: Optional ConfigurationSchemaManager instance.
        """
        self._lock = RLock()
        self._schema_manager = schema_manager or ConfigurationSchemaManager()
        self._regex_cache: Dict[str, Pattern[str]] = {}

        # Metrics
        self._validation_count: int = 0
        self._successful_validations: int = 0
        self._failed_validations: int = 0

    def _get_regex(self, pattern_str: str) -> Pattern[str]:
        """Get or compile regex pattern."""
        if pattern_str not in self._regex_cache:
            self._regex_cache[pattern_str] = re.compile(pattern_str)
        return self._regex_cache[pattern_str]

    def validate_property(self, key: str, value: Any, defn: ConfigurationDefinition) -> Tuple[List[ConfigurationError], List[ConfigurationWarning]]:
        """Validate a single property against definition and constraints.

        Args:
            key: Configuration key string.
            value: Resolved property value.
            defn: Target property definition model.

        Returns:
            Tuple[List[ConfigurationError], List[ConfigurationWarning]]: Discovered errors and warnings.
        """
        errors: List[ConfigurationError] = []
        warnings: List[ConfigurationWarning] = []

        # Required key validation
        if value is None:
            if defn.required:
                errors.append(
                    ConfigurationError(
                        key=key,
                        message=f"Required configuration key '{key}' is missing or None.",
                        error_type="MISSING_REQUIRED_KEY",
                    )
                )
            elif defn.default_value is not None:
                warnings.append(
                    ConfigurationWarning(
                        key=key,
                        message=f"Key '{key}' is missing; defaulting to '{defn.default_value}'.",
                        warning_type="DEFAULT_APPLIED",
                    )
                )
            return errors, warnings

        # Constraint validations
        c: Optional[ConfigurationConstraint] = defn.constraint
        if c is not None:
            # Allowed values
            if c.allowed_values is not None and value not in c.allowed_values:
                errors.append(
                    ConfigurationError(
                        key=key,
                        message=f"Value '{value}' for key '{key}' is not in allowed values {c.allowed_values}.",
                        error_type="ALLOWED_VALUES_VIOLATION",
                    )
                )

            # Minimum value
            if c.min_value is not None and value < c.min_value:
                errors.append(
                    ConfigurationError(
                        key=key,
                        message=f"Value {value} for key '{key}' is less than minimum allowed {c.min_value}.",
                        error_type="MIN_VALUE_VIOLATION",
                    )
                )

            # Maximum value
            if c.max_value is not None and value > c.max_value:
                errors.append(
                    ConfigurationError(
                        key=key,
                        message=f"Value {value} for key '{key}' is greater than maximum allowed {c.max_value}.",
                        error_type="MAX_VALUE_VIOLATION",
                    )
                )

            # String length bounds
            if isinstance(value, str):
                if c.min_length is not None and len(value) < c.min_length:
                    errors.append(
                        ConfigurationError(
                            key=key,
                            message=f"String length {len(value)} for key '{key}' is less than minimum length {c.min_length}.",
                            error_type="MIN_LENGTH_VIOLATION",
                        )
                    )
                if c.max_length is not None and len(value) > c.max_length:
                    errors.append(
                        ConfigurationError(
                            key=key,
                            message=f"String length {len(value)} for key '{key}' is greater than maximum length {c.max_length}.",
                            error_type="MAX_LENGTH_VIOLATION",
                        )
                    )
                # Regex pattern matching
                if c.regex_pattern is not None:
                    regex = self._get_regex(c.regex_pattern)
                    if not regex.match(value):
                        errors.append(
                            ConfigurationError(
                                key=key,
                                message=f"Value '{value}' for key '{key}' does not match pattern '{c.regex_pattern}'.",
                                error_type="REGEX_MISMATCH",
                            )
                        )

        return errors, warnings

    def validate(
        self, values: Optional[Dict[str, Any]] = None, schema: Optional[ConfigurationSchema] = None
    ) -> ConfigurationValidationResult:
        """Validate configuration values against registered schemas.

        Args:
            values: Dictionary of resolved configuration key-value pairs.
            schema: Optional explicit schema override.

        Returns:
            ConfigurationValidationResult: Validation report model.
        """
        with self._lock:
            self._validation_count += 1
            all_values = values or {}
            all_errors: List[ConfigurationError] = []
            all_warnings: List[ConfigurationWarning] = []

            definitions = schema.definitions if schema else self._schema_manager.get_all_definitions()

            for defn in definitions:
                val = all_values.get(defn.key)
                errs, warns = self.validate_property(defn.key, val, defn)
                all_errors.extend(errs)
                all_warnings.extend(warns)

            is_valid = len(all_errors) == 0
            if is_valid:
                self._successful_validations += 1
            else:
                self._failed_validations += 1

            return ConfigurationValidationResult(
                is_valid=is_valid,
                errors=tuple(all_errors),
                warnings=tuple(all_warnings),
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ValidationStatistics:
        """Get validation metrics."""
        with self._lock:
            return ValidationStatistics(
                validation_count=self._validation_count,
                successful_validations=self._successful_validations,
                failed_validations=self._failed_validations,
            )
