"""API Validation Provider Implementation (Phase 15.5).

Thread-safe validation provider aggregating SchemaRegistry, ValidationEngine,
and SerializationManager with lifecycle management, health monitoring,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.validation.interfaces import (
    ISchemaRegistry,
    ISerializationManager,
    IValidationEngine,
    IValidationProvider,
)
from backend.application.api.validation.models import (
    ValidationCapabilities,
    ValidationDiagnostics,
    ValidationHealth,
    ValidationRuntimeState,
    ValidationStatistics,
)
from backend.application.api.validation.schema_registry import SchemaRegistry
from backend.application.api.validation.serialization_manager import (
    SerializationManager,
)
from backend.application.api.validation.validation_engine import (
    ValidationEngine,
)

logger = logging.getLogger(__name__)


class ValidationProvider(IValidationProvider):
    """Production thread-safe validation provider aggregating validation components."""

    def __init__(
        self,
        schema_registry: Optional[ISchemaRegistry] = None,
        validation_engine: Optional[IValidationEngine] = None,
        serialization_manager: Optional[ISerializationManager] = None,
        capabilities: Optional[ValidationCapabilities] = None,
    ) -> None:
        """Initialize ValidationProvider using Constructor Dependency Injection.

        Args:
            schema_registry: Optional ISchemaRegistry implementation instance.
            validation_engine: Optional IValidationEngine implementation instance.
            serialization_manager: Optional ISerializationManager implementation instance.
            capabilities: Optional ValidationCapabilities instance.
        """
        self._lock = RLock()
        self._schema_registry = schema_registry or SchemaRegistry()
        self._validation_engine = validation_engine or ValidationEngine(
            registry=self._schema_registry
        )
        self._serialization_manager = (
            serialization_manager or SerializationManager()
        )
        self._capabilities = capabilities or ValidationCapabilities()

        self._status = ValidationRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> ValidationHealth:
        """Initialize the validation provider and transition state to READY.

        Returns:
            ValidationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                ValidationRuntimeState.INITIALIZING,
                ValidationRuntimeState.READY,
            ):
                return self.health()

            self._status = ValidationRuntimeState.INITIALIZING
            logger.info("ValidationProvider transitioning to INITIALIZING state.")

            self._status = ValidationRuntimeState.READY
            self._total_initializations += 1
            logger.info("ValidationProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> ValidationHealth:
        """Shutdown the validation provider safely and transition state to STOPPED.

        Returns:
            ValidationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == ValidationRuntimeState.STOPPED:
                return self.health()

            self._status = ValidationRuntimeState.STOPPING
            logger.info("ValidationProvider transitioning to STOPPING state.")

            self._status = ValidationRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("ValidationProvider successfully stopped.")
            return self.health()

    def restart(self) -> ValidationHealth:
        """Restart the validation provider by shutting down if active, then initializing.

        Returns:
            ValidationHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("ValidationProvider restarting...")
            if self._status != ValidationRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> ValidationHealth:
        """Get health status evaluation snapshot.

        Returns:
            ValidationHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                ValidationRuntimeState.READY,
                ValidationRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Validation provider is in state: {self._status.value}",)

            return ValidationHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "schemas_count": self._schema_registry.count_schemas(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ValidationStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            ValidationStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            total_schemas = self._schema_registry.count_schemas()

            engine_telemetry = {}
            if hasattr(self._validation_engine, "get_engine_telemetry"):
                engine_telemetry = getattr(
                    self._validation_engine, "get_engine_telemetry"
                )()

            serialization_telemetry = {}
            if hasattr(self._serialization_manager, "get_serialization_telemetry"):
                serialization_telemetry = getattr(
                    self._serialization_manager, "get_serialization_telemetry"
                )()

            return ValidationStatistics(
                total_schemas=total_schemas,
                total_validations=engine_telemetry.get("total_validations", 0),
                passed_validations=engine_telemetry.get("passed_validations", 0),
                failed_validations=engine_telemetry.get("failed_validations", 0),
                total_serializations=serialization_telemetry.get(
                    "total_serializations", 0
                ),
                total_deserializations=serialization_telemetry.get(
                    "total_deserializations", 0
                ),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> ValidationCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            ValidationCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> ValidationDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            ValidationDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            total_schemas = self._schema_registry.count_schemas()
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Registered Schemas: {total_schemas}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return ValidationDiagnostics(
                state=self._status,
                registered_schemas_count=total_schemas,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_schema_registry(self) -> ISchemaRegistry:
        """Get encapsulated schema registry.

        Returns:
            ISchemaRegistry: Schema registry.
        """
        with self._lock:
            return self._schema_registry

    def get_validation_engine(self) -> IValidationEngine:
        """Get encapsulated validation engine.

        Returns:
            IValidationEngine: Validation engine.
        """
        with self._lock:
            return self._validation_engine

    def get_serialization_manager(self) -> ISerializationManager:
        """Get encapsulated serialization manager.

        Returns:
            ISerializationManager: Serialization manager.
        """
        with self._lock:
            return self._serialization_manager
