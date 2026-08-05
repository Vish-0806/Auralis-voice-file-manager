"""API Validation & Serialization Models (Phase 15.5).

Defines immutable Pydantic v2 domain models and enums for the provider-independent
API Validation & Serialization Runtime, including validation rules, fields, schemas,
results, errors, serialization results, capabilities, health, statistics, and diagnostics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ValidationSeverity(str, Enum):
    """Severity levels for validation errors and diagnostic messages."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ValidationState(str, Enum):
    """Resulting state of a validation evaluation operation."""

    VALID = "VALID"
    INVALID = "INVALID"
    SKIPPED = "SKIPPED"


class ValidationRuntimeState(str, Enum):
    """Lifecycle states for the validation runtime."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ValidationRule(BaseModel):
    """Immutable validation rule definition."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    name: str
    rule_type: str = "custom"
    params: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class ValidationField(BaseModel):
    """Immutable schema field specification detailing data types and validation rules."""

    model_config = ConfigDict(frozen=True)

    field_name: str
    field_type: str
    required: bool = True
    rules: Tuple[ValidationRule, ...] = Field(default_factory=tuple)
    default_value: Any = None
    description: str = ""


class ValidationSchema(BaseModel):
    """Immutable collection of validation fields representing a data contract schema."""

    model_config = ConfigDict(frozen=True)

    schema_id: str
    name: str
    version: str = "1.0.0"
    fields: Tuple[ValidationField, ...] = Field(default_factory=tuple)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationError(BaseModel):
    """Immutable record of an individual field validation failure."""

    model_config = ConfigDict(frozen=True)

    error_id: str
    field_name: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    rule_name: str = ""
    invalid_value: Any = None


class ValidationResult(BaseModel):
    """Immutable result object produced by validating data against a schema."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool = True
    state: ValidationState = ValidationState.VALID
    schema_id: str = ""
    errors: Tuple[ValidationError, ...] = Field(default_factory=tuple)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SerializationResult(BaseModel):
    """Immutable result object produced by a serialization or deserialization operation."""

    model_config = ConfigDict(frozen=True)

    is_success: bool = True
    serialized_data: Any = None
    target_type: str = "json_dict"
    error_message: Optional[str] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationContext(BaseModel):
    """Immutable execution context for validation workflows."""

    model_config = ConfigDict(frozen=True)

    context_id: str
    schema_id: str = ""
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationCapabilities(BaseModel):
    """Immutable model declaring supported validation runtime capabilities."""

    model_config = ConfigDict(frozen=True)

    supports_schema_registration: bool = True
    supports_field_validation: bool = True
    supports_type_validation: bool = True
    supports_custom_rules: bool = True
    supports_serialization: bool = True
    supports_deserialization: bool = True
    custom_capabilities: Dict[str, bool] = Field(default_factory=dict)


class ValidationStatistics(BaseModel):
    """Immutable aggregate metrics and statistics for the validation runtime."""

    model_config = ConfigDict(frozen=True)

    total_schemas: int = 0
    total_validations: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    total_serializations: int = 0
    total_deserializations: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ValidationHealth(BaseModel):
    """Immutable health status evaluation of the validation runtime."""

    model_config = ConfigDict(frozen=True)

    is_healthy: bool = True
    state: ValidationRuntimeState = ValidationRuntimeState.UNINITIALIZED
    details: Dict[str, Any] = Field(default_factory=dict)
    issues: Tuple[str, ...] = Field(default_factory=tuple)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationDiagnostics(BaseModel):
    """Immutable diagnostic information for troubleshooting and telemetry."""

    model_config = ConfigDict(frozen=True)

    state: ValidationRuntimeState = ValidationRuntimeState.UNINITIALIZED
    registered_schemas_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread_count: int = 0
    diagnostic_messages: Tuple[str, ...] = Field(default_factory=tuple)
    details: Dict[str, Any] = Field(default_factory=dict)
