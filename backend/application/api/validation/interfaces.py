"""API Validation & Serialization Interfaces (Phase 15.5).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Schema Registry,
Validation Engine, Serialization Manager, Validation Provider, and Validation Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Type

# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from backend.application.api.validation.models import (
    SerializationResult,
    ValidationCapabilities,
    ValidationDiagnostics,
    ValidationHealth,
    ValidationResult,
    ValidationSchema,
    ValidationStatistics,
)


class ISchemaRegistry(ABC):
    """Abstract interface for the Validation Schema Registry."""

    @abstractmethod
    def register_schema(self, schema: ValidationSchema) -> ValidationSchema:
        """Register a new validation schema.

        Args:
            schema: Immutable ValidationSchema instance.

        Returns:
            ValidationSchema: Registered schema.

        Raises:
            SchemaRegistrationException: If registration fails or schema_id exists.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_schema(self, schema_id: str) -> Optional[ValidationSchema]:
        """Unregister a schema by schema ID.

        Args:
            schema_id: Unique schema identifier.

        Returns:
            Optional[ValidationSchema]: Removed schema if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_schema(self, schema_id: str) -> Optional[ValidationSchema]:
        """Look up a schema by ID.

        Args:
            schema_id: Unique schema identifier.

        Returns:
            Optional[ValidationSchema]: Schema model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_schemas(self) -> Tuple[ValidationSchema, ...]:
        """List all registered schemas.

        Returns:
            Tuple[ValidationSchema, ...]: Tuple of registered schemas.
        """
        raise NotImplementedError

    @abstractmethod
    def count_schemas(self) -> int:
        """Get total count of registered schemas.

        Returns:
            int: Schema count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered schemas from the registry."""
        raise NotImplementedError


class IValidationEngine(ABC):
    """Abstract interface for the Validation Engine."""

    @abstractmethod
    def validate(
        self, schema_id: str, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate input data dictionary against a registered schema ID.

        Args:
            schema_id: Target registered schema ID.
            data: Input dictionary to validate.

        Returns:
            ValidationResult: Result snapshot of validation operation.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_with_schema(
        self, schema: ValidationSchema, data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate input data dictionary directly against a schema model.

        Args:
            schema: Target ValidationSchema instance.
            data: Input dictionary to validate.

        Returns:
            ValidationResult: Result snapshot of validation operation.
        """
        raise NotImplementedError


class ISerializationManager(ABC):
    """Abstract interface for the Serialization Manager."""

    @abstractmethod
    def serialize(self, obj: Any) -> SerializationResult:
        """Serialize an object or Pydantic model into a serializable data structure.

        Args:
            obj: Object or model instance to serialize.

        Returns:
            SerializationResult: Result snapshot of serialization.
        """
        raise NotImplementedError

    @abstractmethod
    def deserialize(
        self, data: Dict[str, Any], model_class: Type[BaseModel]
    ) -> SerializationResult:
        """Deserialize a data dictionary into a target Pydantic model class.

        Args:
            data: Input dictionary.
            model_class: Target Pydantic model class.

        Returns:
            SerializationResult: Result snapshot of deserialization containing model instance.
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """Helper to convert any object or model to a plain dictionary.

        Args:
            obj: Target object.

        Returns:
            Dict[str, Any]: Dictionary representation.
        """
        raise NotImplementedError


class IValidationProvider(ABC):
    """Abstract interface for the Validation Provider."""

    @abstractmethod
    def initialize(self) -> ValidationHealth:
        """Initialize the validation provider.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ValidationHealth:
        """Shutdown the validation provider safely.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ValidationHealth:
        """Restart the validation provider.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ValidationHealth:
        """Get health evaluation snapshot.

        Returns:
            ValidationHealth: Health evaluation.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ValidationStatistics:
        """Get aggregate statistics.

        Returns:
            ValidationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ValidationCapabilities:
        """Get declared capabilities.

        Returns:
            ValidationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ValidationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            ValidationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_schema_registry(self) -> ISchemaRegistry:
        """Get encapsulated schema registry.

        Returns:
            ISchemaRegistry: Schema registry.
        """
        raise NotImplementedError

    @abstractmethod
    def get_validation_engine(self) -> IValidationEngine:
        """Get encapsulated validation engine.

        Returns:
            IValidationEngine: Validation engine.
        """
        raise NotImplementedError

    @abstractmethod
    def get_serialization_manager(self) -> ISerializationManager:
        """Get encapsulated serialization manager.

        Returns:
            ISerializationManager: Serialization manager.
        """
        raise NotImplementedError


class IValidationRuntime(ABC):
    """Abstract interface for the Validation Runtime."""

    @abstractmethod
    def initialize(self) -> ValidationHealth:
        """Initialize the validation runtime.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ValidationHealth:
        """Shutdown the validation runtime safely.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> ValidationHealth:
        """Restart the validation runtime.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ValidationHealth:
        """Get health evaluation snapshot.

        Returns:
            ValidationHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> ValidationStatistics:
        """Get aggregate statistics.

        Returns:
            ValidationStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> ValidationCapabilities:
        """Get declared capabilities.

        Returns:
            ValidationCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> ValidationDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            ValidationDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IValidationProvider:
        """Get encapsulated validation provider.

        Returns:
            IValidationProvider: Validation provider.
        """
        raise NotImplementedError
