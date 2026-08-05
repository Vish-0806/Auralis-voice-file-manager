"""API Schema Registry Implementation (Phase 15.5).

Thread-safe schema registry for storing, querying, and unregistering validation schemas
with duplicate detection and registration telemetry.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Tuple

from backend.application.api.validation.exceptions import (
    SchemaRegistrationException,
)
from backend.application.api.validation.interfaces import ISchemaRegistry
from backend.application.api.validation.models import ValidationSchema

logger = logging.getLogger(__name__)


class SchemaRegistry(ISchemaRegistry):
    """Thread-safe in-memory registry for storing validation schemas."""

    def __init__(self) -> None:
        """Initialize SchemaRegistry using Constructor Dependency Injection."""
        self._lock = RLock()
        self._schemas: Dict[str, ValidationSchema] = {}

        self._total_registrations = 0
        self._total_unregistrations = 0
        self._total_clears = 0

    def register_schema(self, schema: ValidationSchema) -> ValidationSchema:
        """Register a new validation schema in the registry.

        Args:
            schema: Immutable ValidationSchema instance.

        Returns:
            ValidationSchema: Registered schema.

        Raises:
            SchemaRegistrationException: If schema_id is already registered.
        """
        with self._lock:
            if schema.schema_id in self._schemas:
                raise SchemaRegistrationException(
                    f"Validation schema with ID '{schema.schema_id}' is already registered."
                )

            self._schemas[schema.schema_id] = schema
            self._total_registrations += 1
            logger.info("Registered validation schema ID '%s' (%s).", schema.schema_id, schema.name)
            return schema

    def unregister_schema(self, schema_id: str) -> Optional[ValidationSchema]:
        """Unregister a schema by schema ID.

        Args:
            schema_id: Unique schema identifier.

        Returns:
            Optional[ValidationSchema]: Unregistered schema if present, else None.
        """
        with self._lock:
            schema = self._schemas.pop(schema_id, None)
            if schema is not None:
                self._total_unregistrations += 1
                logger.info("Unregistered validation schema ID '%s'.", schema_id)
            return schema

    def lookup_schema(self, schema_id: str) -> Optional[ValidationSchema]:
        """Look up a schema by ID.

        Args:
            schema_id: Unique schema identifier.

        Returns:
            Optional[ValidationSchema]: ValidationSchema if found, else None.
        """
        with self._lock:
            return self._schemas.get(schema_id)

    def list_schemas(self) -> Tuple[ValidationSchema, ...]:
        """List all registered validation schemas.

        Returns:
            Tuple[ValidationSchema, ...]: Immutable tuple of schemas.
        """
        with self._lock:
            return tuple(self._schemas.values())

    def count_schemas(self) -> int:
        """Get total count of registered schemas.

        Returns:
            int: Number of schemas.
        """
        with self._lock:
            return len(self._schemas)

    def clear(self) -> None:
        """Clear all registered schemas from the registry."""
        with self._lock:
            self._schemas.clear()
            self._total_clears += 1
            logger.info("SchemaRegistry cleared.")

    def get_registry_telemetry(self) -> Dict[str, int]:
        """Get internal registry telemetry counters under lock."""
        with self._lock:
            return {
                "total_registrations": self._total_registrations,
                "total_unregistrations": self._total_unregistrations,
                "total_clears": self._total_clears,
                "current_count": len(self._schemas),
            }
