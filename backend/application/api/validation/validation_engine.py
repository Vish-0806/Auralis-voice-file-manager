"""API Validation Engine Implementation (Phase 15.5).

Thread-safe deterministic validation engine evaluating data against schema specifications,
field requirements, type assertions, and rule conditions without HTTP or FastAPI dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, List, Optional
import uuid

from backend.application.api.validation.interfaces import (
    ISchemaRegistry,
    IValidationEngine,
)
from backend.application.api.validation.models import (
    ValidationError,
    ValidationResult,
    ValidationSchema,
    ValidationSeverity,
    ValidationState,
)
from backend.application.api.validation.schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


class ValidationEngine(IValidationEngine):
    """Thread-safe validation engine validating dictionary data against ValidationSchema objects."""

    def __init__(self, registry: Optional[ISchemaRegistry] = None) -> None:
        """Initialize ValidationEngine using Constructor Dependency Injection.

        Args:
            registry: Optional ISchemaRegistry implementation instance.
        """
        self._lock = RLock()
        self._registry = registry or SchemaRegistry()

        self._total_validations = 0
        self._passed_validations = 0
        self._failed_validations = 0

    def validate(
        self, schema_id: str, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate input dictionary against a registered schema ID.

        Args:
            schema_id: Target registered schema ID.
            data: Input dictionary to validate.

        Returns:
            ValidationResult: Result snapshot of the validation operation.
        """
        with self._lock:
            schema = self._registry.lookup_schema(schema_id)
            if schema is None:
                self._total_validations += 1
                self._failed_validations += 1
                err = ValidationError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    field_name="schema_id",
                    message=f"Schema with ID '{schema_id}' was not found in registry.",
                    severity=ValidationSeverity.ERROR,
                    rule_name="schema_exists",
                    invalid_value=schema_id,
                )
                return ValidationResult(
                    is_valid=False,
                    state=ValidationState.INVALID,
                    schema_id=schema_id,
                    errors=(err,),
                    validated_at=datetime.now(timezone.utc),
                )

            return self.validate_with_schema(schema=schema, data=data)

    def validate_with_schema(
        self, schema: ValidationSchema, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate input dictionary directly against a schema model.

        Args:
            schema: Target ValidationSchema model instance.
            data: Input dictionary to validate.

        Returns:
            ValidationResult: Result snapshot of the validation operation.
        """
        with self._lock:
            self._total_validations += 1
            errors: List[ValidationError] = []

            for field in schema.fields:
                val = data.get(field.field_name)

                # Required field check
                if field.required and (val is None or (field.field_name not in data)):
                    err_id = f"err_{uuid.uuid4().hex[:8]}"
                    errors.append(
                        ValidationError(
                            error_id=err_id,
                            field_name=field.field_name,
                            message=f"Field '{field.field_name}' is required but missing or null.",
                            severity=ValidationSeverity.ERROR,
                            rule_name="required",
                            invalid_value=val,
                        )
                    )
                    continue

                if val is None:
                    continue

                # Type assertion check
                type_err = self._check_field_type(field.field_name, field.field_type, val)
                if type_err:
                    errors.append(type_err)
                    continue

                # Custom rule evaluation
                for rule in field.rules:
                    rule_err = self._evaluate_rule(field.field_name, rule, val)
                    if rule_err:
                        errors.append(rule_err)

            is_valid = len(errors) == 0
            if is_valid:
                self._passed_validations += 1
            else:
                self._failed_validations += 1

            state = ValidationState.VALID if is_valid else ValidationState.INVALID
            logger.info(
                "Validated data against schema '%s' -> %s (%d errors).",
                schema.schema_id,
                state.value,
                len(errors),
            )

            return ValidationResult(
                is_valid=is_valid,
                state=state,
                schema_id=schema.schema_id,
                errors=tuple(errors),
                validated_at=datetime.now(timezone.utc),
            )

    def _check_field_type(
        self, field_name: str, field_type: str, value: Any
    ) -> Optional[ValidationError]:
        """Internal type checking helper under lock."""
        target_type = field_type.lower()

        type_map = {
            "str": str,
            "string": str,
            "int": int,
            "integer": int,
            "float": (int, float),
            "number": (int, float),
            "bool": bool,
            "boolean": bool,
            "dict": dict,
            "object": dict,
            "list": list,
            "array": list,
        }

        expected_type = type_map.get(target_type)

        # Reject bool when int is expected since bool is a subclass of int in Python
        if target_type in ("int", "integer") and isinstance(value, bool):
            err_id = f"err_{uuid.uuid4().hex[:8]}"
            return ValidationError(
                error_id=err_id,
                field_name=field_name,
                message=f"Field '{field_name}' expected type '{field_type}', got 'bool'.",
                severity=ValidationSeverity.ERROR,
                rule_name="type_check",
                invalid_value=value,
            )

        if expected_type and not isinstance(value, expected_type):
            err_id = f"err_{uuid.uuid4().hex[:8]}"
            return ValidationError(
                error_id=err_id,
                field_name=field_name,
                message=f"Field '{field_name}' expected type '{field_type}', got '{type(value).__name__}'.",
                severity=ValidationSeverity.ERROR,
                rule_name="type_check",
                invalid_value=value,
            )

        return None

    def _evaluate_rule(
        self, field_name: str, rule: Any, value: Any
    ) -> Optional[ValidationError]:
        """Internal rule evaluation helper under lock."""
        r_type = rule.rule_type.lower()

        if r_type == "min_length" and isinstance(value, (str, list)):
            min_len = rule.params.get("min_length", 0)
            if len(value) < min_len:
                return ValidationError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    field_name=field_name,
                    message=f"Field '{field_name}' length {len(value)} is below minimum {min_len}.",
                    severity=ValidationSeverity.ERROR,
                    rule_name=rule.name,
                    invalid_value=value,
                )

        elif r_type == "max_length" and isinstance(value, (str, list)):
            max_len = rule.params.get("max_length", 999999)
            if len(value) > max_len:
                return ValidationError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    field_name=field_name,
                    message=f"Field '{field_name}' length {len(value)} exceeds maximum {max_len}.",
                    severity=ValidationSeverity.ERROR,
                    rule_name=rule.name,
                    invalid_value=value,
                )

        elif r_type == "min" and isinstance(value, (int, float)):
            min_val = rule.params.get("min", 0)
            if value < min_val:
                return ValidationError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    field_name=field_name,
                    message=f"Field '{field_name}' value {value} is below minimum {min_val}.",
                    severity=ValidationSeverity.ERROR,
                    rule_name=rule.name,
                    invalid_value=value,
                )

        elif r_type == "max" and isinstance(value, (int, float)):
            max_val = rule.params.get("max", 999999)
            if value > max_val:
                return ValidationError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    field_name=field_name,
                    message=f"Field '{field_name}' value {value} exceeds maximum {max_val}.",
                    severity=ValidationSeverity.ERROR,
                    rule_name=rule.name,
                    invalid_value=value,
                )

        return None

    def get_engine_telemetry(self) -> Dict[str, int]:
        """Get engine validation telemetry counters under lock."""
        with self._lock:
            return {
                "total_validations": self._total_validations,
                "passed_validations": self._passed_validations,
                "failed_validations": self._failed_validations,
            }
