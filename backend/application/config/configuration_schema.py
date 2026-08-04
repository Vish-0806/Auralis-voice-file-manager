"""Configuration Schema Manager (Phase 14.3.3).

Thread-safe manager for registering, organizing, and caching configuration schemas and property definitions.
"""

import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple

from backend.application.config.exceptions import ConfigurationValidationError
from backend.application.config.models import ConfigurationDefinition, ConfigurationSchema

logger = logging.getLogger(__name__)


class ConfigurationSchemaManager:
    """Production thread-safe configuration schema manager with property definition caching."""

    def __init__(self) -> None:
        """Initialize ConfigurationSchemaManager."""
        self._lock = RLock()
        self._schemas: Dict[str, ConfigurationSchema] = {}
        self._definitions_cache: Dict[str, ConfigurationDefinition] = {}

    def register_schema(self, schema: ConfigurationSchema) -> bool:
        """Register a configuration schema.

        Args:
            schema: Target ConfigurationSchema instance.

        Returns:
            bool: True if registered.

        Raises:
            ConfigurationValidationError: If schema is invalid or duplicate schema_name.
        """
        if schema is None or not schema.schema_name:
            raise ConfigurationValidationError("Cannot register invalid or nameless configuration schema.")

        with self._lock:
            name = schema.schema_name
            if name in self._schemas:
                raise ConfigurationValidationError(f"Configuration schema '{name}' is already registered.")

            self._schemas[name] = schema
            for defn in schema.definitions:
                self._definitions_cache[defn.key] = defn

            logger.info(
                "Registered configuration schema '%s' with %d definitions.", name, len(schema.definitions)
            )
            return True

    def unregister_schema(self, schema_name: str) -> bool:
        """Unregister a configuration schema by name.

        Args:
            schema_name: Target schema name.

        Returns:
            bool: True if unregistered.
        """
        with self._lock:
            if schema_name in self._schemas:
                schema = self._schemas.pop(schema_name)
                # Rebuild cache
                self._definitions_cache.clear()
                for s in self._schemas.values():
                    for defn in s.definitions:
                        self._definitions_cache[defn.key] = defn
                logger.info("Unregistered configuration schema '%s'.", schema_name)
                return True
            return False

    def contains(self, schema_name: str) -> bool:
        """Check if a schema is registered."""
        with self._lock:
            return schema_name in self._schemas

    def get_schema(self, schema_name: str) -> Optional[ConfigurationSchema]:
        """Get registered schema by name."""
        with self._lock:
            return self._schemas.get(schema_name)

    def list_schemas(self) -> Tuple[ConfigurationSchema, ...]:
        """List all registered configuration schemas."""
        with self._lock:
            return tuple(self._schemas.values())

    def get_definition(self, key: str) -> Optional[ConfigurationDefinition]:
        """Get cached ConfigurationDefinition by key."""
        with self._lock:
            return self._definitions_cache.get(key)

    def get_all_definitions(self) -> Tuple[ConfigurationDefinition, ...]:
        """Get all cached property definitions."""
        with self._lock:
            return tuple(self._definitions_cache.values())

    def clear(self) -> None:
        """Clear all registered schemas and cached definitions."""
        with self._lock:
            self._schemas.clear()
            self._definitions_cache.clear()
            logger.info("Cleared all registered configuration schemas.")
