"""Application Layer Interfaces (Phase 14.1).

Defines Abstract Base Classes (ABCs) establishing explicit design contracts for
application runtime management, service providers, bootstrap managers, runtime registries,
initialization managers, and startup validators.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

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


class IApplicationRuntime(ABC):
    """Abstract interface for the Application Runtime Coordinator."""

    @abstractmethod
    def initialize(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Initialize the application runtime and associated subsystems.

        Args:
            config: Optional application configuration override.

        Returns:
            ApplicationState: Updated state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def start(self) -> ApplicationState:
        """Start the application runtime and transition to RUNNING state.

        Returns:
            ApplicationState: Updated state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> ApplicationState:
        """Stop the application runtime safely.

        Returns:
            ApplicationState: Updated state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> ApplicationState:
        """Shutdown the application runtime completely and release resources.

        Returns:
            ApplicationState: Updated state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> ApplicationState:
        """Get the current application state snapshot.

        Returns:
            ApplicationState: Current state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_health(self) -> ApplicationHealth:
        """Get current health assessment of the application runtime.

        Returns:
            ApplicationHealth: Health evaluation.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_statistics(self) -> ApplicationStatistics:
        """Get current application runtime statistics.

        Returns:
            ApplicationStatistics: Runtime metrics.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_diagnostics(self) -> ApplicationDiagnostics:
        """Get detailed telemetry and diagnostic information.

        Returns:
            ApplicationDiagnostics: System diagnostics.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> ApplicationContext:
        """Get current execution context.

        Returns:
            ApplicationContext: Active application context.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_capabilities(self) -> ApplicationCapabilities:
        """Get application capabilities supported by the runtime.

        Returns:
            ApplicationCapabilities: Enabled capability flags.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError


class IApplicationProvider(ABC):
    """Abstract interface for Application Service Provider."""

    @abstractmethod
    def get_runtime(self) -> IApplicationRuntime:
        """Get the active application runtime instance.

        Returns:
            IApplicationRuntime: Configured runtime instance.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_configuration(self) -> ApplicationConfiguration:
        """Get active application configuration.

        Returns:
            ApplicationConfiguration: Active configuration instance.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> ApplicationContext:
        """Get active application context.

        Returns:
            ApplicationContext: Execution context.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_capabilities(self) -> ApplicationCapabilities:
        """Get declared application capabilities.

        Returns:
            ApplicationCapabilities: Application capabilities.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError


class IBootstrapManager(ABC):
    """Abstract interface for Application Bootstrap Manager."""

    @abstractmethod
    def bootstrap(self, config: ApplicationConfiguration) -> ApplicationState:
        """Bootstrap all application components and subsystems.

        Args:
            config: Application configuration.

        Returns:
            ApplicationState: Post-bootstrap state.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def teardown(self) -> ApplicationState:
        """Teardown bootstrapped components and release resources.

        Returns:
            ApplicationState: Post-teardown state.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def is_bootstrapped(self) -> bool:
        """Check if bootstrapping was completed successfully.

        Returns:
            bool: True if bootstrapped, False otherwise.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_bootstrap_state(self) -> ApplicationState:
        """Get current bootstrap state snapshot.

        Returns:
            ApplicationState: Bootstrap state snapshot.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError


class IRuntimeRegistry(ABC):
    """Abstract interface for Subsystem Runtime Registry."""

    @abstractmethod
    def register(self, registration: RuntimeRegistration) -> bool:
        """Register a subsystem runtime.

        Args:
            registration: Subsystem registration metadata.

        Returns:
            bool: True if registration succeeded, False otherwise.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister(self, name: str) -> bool:
        """Unregister a subsystem runtime by name.

        Args:
            name: Name of the subsystem runtime.

        Returns:
            bool: True if unregistration succeeded, False otherwise.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_registration(self, name: str) -> Optional[RuntimeRegistration]:
        """Retrieve registration record for a subsystem by name.

        Args:
            name: Name of the subsystem runtime.

        Returns:
            Optional[RuntimeRegistration]: Registration record if present.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def list_registrations(self) -> Tuple[RuntimeRegistration, ...]:
        """List all active runtime registrations.

        Returns:
            Tuple[RuntimeRegistration, ...]: Immutable tuple of registrations.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def is_registered(self) -> bool:
        """Check if a subsystem runtime is registered by name.

        Args:
            name: Name of the subsystem.

        Returns:
            bool: True if registered, False otherwise.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered subsystem runtimes.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError


class IInitializationManager(ABC):
    """Abstract interface for Application Initialization Manager."""

    @abstractmethod
    def initialize_all(self, context: ApplicationContext) -> bool:
        """Initialize all managed subsystems in correct dependency order.

        Args:
            context: Application context snapshot.

        Returns:
            bool: True if initialization succeeded for all subsystems.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if initialization has completed successfully.

        Returns:
            bool: True if initialized.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def get_initialized_components(self) -> Tuple[str, ...]:
        """Get tuple of component names that have completed initialization.

        Returns:
            Tuple[str, ...]: Component names.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError


class IStartupValidator(ABC):
    """Abstract interface for Application Startup Validator."""

    @abstractmethod
    def validate_environment(self) -> bool:
        """Validate execution environment settings and system dependencies.

        Returns:
            bool: True if environment is valid.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_configuration(self, config: ApplicationConfiguration) -> bool:
        """Validate application configuration structure and values.

        Args:
            config: Application configuration to validate.

        Returns:
            bool: True if configuration is valid.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_runtime_dependencies(self) -> bool:
        """Validate required runtime subsystem dependencies.

        Returns:
            bool: True if dependencies are satisfied.

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError

    @abstractmethod
    def run_all_validations(
        self, config: ApplicationConfiguration
    ) -> Tuple[str, ...]:
        """Run all startup validations and return tuple of validation error strings.

        Args:
            config: Application configuration.

        Returns:
            Tuple[str, ...]: Validation error messages (empty if all pass).

        Raises:
            NotImplementedError: Pending phase implementation.
        """
        raise NotImplementedError
