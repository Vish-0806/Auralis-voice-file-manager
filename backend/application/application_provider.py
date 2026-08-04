"""Application Service Provider (Phase 14.1).

High-level provider aggregating RuntimeRegistry, BootstrapManager, StartupValidator,
InitializationManager, ApplicationRuntime, and configuration details.
"""

import logging
from threading import RLock
from typing import Optional, Tuple

from backend.application.bootstrap_manager import BootstrapManager
from backend.application.initialization_manager import InitializationManager
from backend.application.interfaces import IApplicationProvider, IApplicationRuntime
from backend.application.models import (
    ApplicationCapabilities,
    ApplicationConfiguration,
    ApplicationContext,
    ApplicationDiagnostics,
    ApplicationHealth,
    ApplicationState,
    ApplicationStatistics,
    RuntimeRegistration,
)
from backend.application.runtime_registry import RuntimeRegistry
from backend.application.startup_validator import StartupValidator

logger = logging.getLogger(__name__)


class ApplicationProvider(IApplicationProvider):
    """Production application provider encapsulating subsystems and runtime orchestration."""

    def __init__(
        self,
        runtime: Optional[IApplicationRuntime] = None,
        config: Optional[ApplicationConfiguration] = None,
        runtime_registry: Optional[RuntimeRegistry] = None,
        bootstrap_manager: Optional[BootstrapManager] = None,
        startup_validator: Optional[StartupValidator] = None,
        initialization_manager: Optional[InitializationManager] = None,
    ) -> None:
        """Initialize ApplicationProvider using Constructor Dependency Injection.

        Args:
            runtime: Optional ApplicationRuntime coordinator instance.
            config: Optional application configuration.
            runtime_registry: Optional runtime registry instance.
            bootstrap_manager: Optional bootstrap manager instance.
            startup_validator: Optional startup validator instance.
            initialization_manager: Optional initialization manager instance.
        """
        self._lock = RLock()
        self._config = config or ApplicationConfiguration()
        self._runtime_registry = runtime_registry or RuntimeRegistry()
        self._startup_validator = startup_validator or StartupValidator()
        self._initialization_manager = (
            initialization_manager
            or InitializationManager(runtime_registry=self._runtime_registry)
        )
        self._bootstrap_manager = (
            bootstrap_manager
            or BootstrapManager(
                initialization_manager=self._initialization_manager,
                startup_validator=self._startup_validator,
                runtime_registry=self._runtime_registry,
            )
        )
        self._runtime = runtime

    def _get_or_create_runtime(self) -> IApplicationRuntime:
        """Helper to get or lazily instantiate ApplicationRuntime."""
        with self._lock:
            if self._runtime is None:
                from backend.application.application_runtime import ApplicationRuntime

                self._runtime = ApplicationRuntime(
                    bootstrap_manager=self._bootstrap_manager,
                    runtime_registry=self._runtime_registry,
                    initialization_manager=self._initialization_manager,
                    startup_validator=self._startup_validator,
                    config=self._config,
                )
            return self._runtime

    def initialize(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Initialize the application runtime and associated subsystems.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Updated state snapshot.
        """
        with self._lock:
            if config:
                self._config = config
            return self._get_or_create_runtime().initialize(config)

    def shutdown(self) -> ApplicationState:
        """Shutdown the application runtime completely.

        Returns:
            ApplicationState: Updated state snapshot.
        """
        with self._lock:
            return self._get_or_create_runtime().shutdown()

    def restart(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Restart the application runtime.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Updated state snapshot.
        """
        with self._lock:
            if config:
                self._config = config
            runtime = self._get_or_create_runtime()
            if hasattr(runtime, "restart"):
                return runtime.restart(config)  # type: ignore[attr-defined]
            runtime.shutdown()
            return runtime.initialize(config)

    def boot(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Boot all application components via BootstrapManager.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Post-boot state snapshot.
        """
        with self._lock:
            cfg = config or self._config
            return self._bootstrap_manager.boot(cfg)

    def validate(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationDiagnostics:
        """Perform pre-startup validation checks.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationDiagnostics: System diagnostics if validation succeeds.
        """
        with self._lock:
            cfg = config or self._config
            return self._startup_validator.validate_startup(
                cfg, registry=self._runtime_registry
            )

    def health(self) -> ApplicationHealth:
        """Get aggregate application health.

        Returns:
            ApplicationHealth: Health snapshot.
        """
        with self._lock:
            return self._get_or_create_runtime().get_health()

    def statistics(self) -> ApplicationStatistics:
        """Get aggregated runtime statistics.

        Returns:
            ApplicationStatistics: Aggregated statistics metrics.
        """
        with self._lock:
            return self._get_or_create_runtime().get_statistics()

    def capabilities(self) -> ApplicationCapabilities:
        """Get application capability definitions.

        Returns:
            ApplicationCapabilities: Declared capability flags.
        """
        with self._lock:
            return self._get_or_create_runtime().get_capabilities()

    def diagnostics(self) -> ApplicationDiagnostics:
        """Get telemetry and diagnostic information.

        Returns:
            ApplicationDiagnostics: Diagnostic information.
        """
        with self._lock:
            return self._get_or_create_runtime().get_diagnostics()

    def register_runtime(self, registration: RuntimeRegistration) -> bool:
        """Register a subsystem runtime in the registry.

        Args:
            registration: Subsystem runtime registration metadata.

        Returns:
            bool: True if registration succeeded.
        """
        with self._lock:
            return self._runtime_registry.register_runtime(registration)

    def unregister_runtime(self, name: str) -> bool:
        """Unregister a subsystem runtime from the registry by name.

        Args:
            name: Subsystem name.

        Returns:
            bool: True if unregistered.
        """
        with self._lock:
            return self._runtime_registry.unregister_runtime(name)

    def get_runtime(self, name: str = "") -> Optional[RuntimeRegistration] | IApplicationRuntime:  # type: ignore[override]
        """Get runtime registration by name OR active IApplicationRuntime if name empty.

        Args:
            name: Optional subsystem runtime name.

        Returns:
            RuntimeRegistration or IApplicationRuntime.
        """
        with self._lock:
            if not name:
                return self._get_or_create_runtime()
            return self._runtime_registry.get_runtime(name)

    def list_runtimes(self) -> Tuple[RuntimeRegistration, ...]:
        """List all registered subsystem runtimes.

        Returns:
            Tuple[RuntimeRegistration, ...]: Active registrations.
        """
        with self._lock:
            return self._runtime_registry.list_runtimes()

    def get_configuration(self) -> ApplicationConfiguration:
        """Get active application configuration (IApplicationProvider interface).

        Returns:
            ApplicationConfiguration: Active configuration instance.
        """
        with self._lock:
            return self._config

    def get_context(self) -> ApplicationContext:
        """Get active application execution context (IApplicationProvider interface).

        Returns:
            ApplicationContext: Execution context instance.
        """
        with self._lock:
            return self._get_or_create_runtime().get_context()

    def get_capabilities(self) -> ApplicationCapabilities:
        """Get active application capabilities (IApplicationProvider interface).

        Returns:
            ApplicationCapabilities: Application capabilities.
        """
        return self.capabilities()
