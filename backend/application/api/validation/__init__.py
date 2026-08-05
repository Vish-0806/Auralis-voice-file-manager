"""API Validation & Serialization Runtime Package (Phase 15.5).

Provider-independent Validation & Serialization Runtime establishing models,
exceptions, ABC interfaces, schema registry, validation engine, serialization manager,
validation provider, runtime coordinator, and singleton accessors.
"""

from backend.application.api.validation.exceptions import (
    DeserializationException,
    SchemaRegistrationException,
    SerializationException,
    ValidationException,
    ValidationFailureException,
)
from backend.application.api.validation.interfaces import (
    ISchemaRegistry,
    ISerializationManager,
    IValidationEngine,
    IValidationProvider,
    IValidationRuntime,
)
from backend.application.api.validation.models import (
    SerializationResult,
    ValidationCapabilities,
    ValidationContext,
    ValidationDiagnostics,
    ValidationError,
    ValidationField,
    ValidationHealth,
    ValidationResult,
    ValidationRule,
    ValidationRuntimeState,
    ValidationSchema,
    ValidationSeverity,
    ValidationState,
    ValidationStatistics,
)
from backend.application.api.validation.runtime import (
    get_validation_provider,
    get_validation_runtime,
    reset_validation_provider,
    reset_validation_runtime,
    set_validation_provider,
    set_validation_runtime,
)
from backend.application.api.validation.schema_registry import SchemaRegistry
from backend.application.api.validation.serialization_manager import (
    SerializationManager,
)
from backend.application.api.validation.validation_engine import (
    ValidationEngine,
)
from backend.application.api.validation.validation_provider import (
    ValidationProvider,
)
from backend.application.api.validation.validation_runtime import (
    ValidationRuntime,
)

__all__ = [
    # Models & Enums
    "ValidationSeverity",
    "ValidationState",
    "ValidationRuntimeState",
    "ValidationRule",
    "ValidationField",
    "ValidationSchema",
    "ValidationError",
    "ValidationResult",
    "SerializationResult",
    "ValidationContext",
    "ValidationCapabilities",
    "ValidationStatistics",
    "ValidationHealth",
    "ValidationDiagnostics",
    # Exceptions
    "ValidationException",
    "SchemaRegistrationException",
    "ValidationFailureException",
    "SerializationException",
    "DeserializationException",
    # Interfaces
    "ISchemaRegistry",
    "IValidationEngine",
    "ISerializationManager",
    "IValidationProvider",
    "IValidationRuntime",
    # Implementations
    "SchemaRegistry",
    "ValidationEngine",
    "SerializationManager",
    "ValidationProvider",
    "ValidationRuntime",
    # Runtime Helpers
    "get_validation_runtime",
    "set_validation_runtime",
    "reset_validation_runtime",
    "get_validation_provider",
    "set_validation_provider",
    "reset_validation_provider",
]
