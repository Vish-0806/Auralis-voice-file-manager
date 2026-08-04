"""Application Runtime Coordinator (Phase 14.1).

Production Application Runtime manager responsible for lifecycle orchestration, state transitions,
health aggregation, statistics collection, diagnostics, and sub-manager owner.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, Optional, Tuple

from backend.application.bootstrap_manager import BootstrapManager
from backend.application.exceptions import (
    ApplicationBootstrapError,
    InitializationError,
    StartupValidationError,
)
from backend.application.initialization_manager import InitializationManager
from backend.application.interfaces import IApplicationRuntime
from backend.application.models import (
    ApplicationCapabilities,
    ApplicationConfiguration,
    ApplicationContext,
    ApplicationDiagnostics,
    ApplicationHealth,
    ApplicationLifecycleState,
    ApplicationState,
    ApplicationStatistics,
    RuntimeRegistration,
)
from backend.application.runtime_registry import RuntimeRegistry
from backend.application.startup_validator import StartupValidator

logger = logging.getLogger(__name__)


class ApplicationRuntime(IApplicationRuntime):
    """Central production lifecycle manager and runtime coordinator for Auralis."""

    def __init__(
        self,
        bootstrap_manager: Optional[BootstrapManager] = None,
        runtime_registry: Optional[RuntimeRegistry] = None,
        initialization_manager: Optional[InitializationManager] = None,
        startup_validator: Optional[StartupValidator] = None,
        config: Optional[ApplicationConfiguration] = None,
    ) -> None:
        """Initialize ApplicationRuntime using Constructor Dependency Injection.

        Args:
            bootstrap_manager: Optional bootstrap manager instance.
            runtime_registry: Optional runtime registry instance.
            initialization_manager: Optional initialization manager instance.
            startup_validator: Optional startup validator instance.
            config: Optional application configuration instance.
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

        # Operational State
        self._status: ApplicationLifecycleState = ApplicationLifecycleState.UNINITIALIZED
        self._start_time: Optional[datetime] = None
        self._restart_count: int = 0
        self._context: ApplicationContext = ApplicationContext(
            app_id=self._config.app_name,
            working_directory=".",
        )

    def status(self) -> ApplicationLifecycleState:
        """Get the current application lifecycle status enum.

        Returns:
            ApplicationLifecycleState: Active state enum value.
        """
        with self._lock:
            return self._status

    def state(self) -> ApplicationState:
        """Get the current application state snapshot.

        Returns:
            ApplicationState: Immutable state model.
        """
        with self._lock:
            uptime = 0.0
            if self._start_time and self._status == ApplicationLifecycleState.RUNNING:
                uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

            return ApplicationState(
                status=self._status,
                is_active=(self._status == ApplicationLifecycleState.RUNNING),
                is_healthy=(self._status not in (ApplicationLifecycleState.FAILED, ApplicationLifecycleState.DEGRADED)),
                start_time=self._start_time,
                uptime_seconds=uptime,
                metadata={"config_name": self._config.app_name, "version": self._config.version},
            )

    def get_state(self) -> ApplicationState:
        """Get the current application state snapshot (IApplicationRuntime interface).

        Returns:
            ApplicationState: Current state snapshot.
        """
        return self.state()

    def boot(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Execute boot sequence via BootstrapManager.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Post-boot application state.
        """
        with self._lock:
            cfg = config or self._config
            boot_state = self._bootstrap_manager.boot(cfg)
            self._status = boot_state.status
            if boot_state.is_active:
                self._start_time = self._bootstrap_manager.boot_start_time
            return self.state()

    def initialize(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Initialize the application runtime executing full lifecycle state transitions.

        Lifecycle sequence:
        UNINITIALIZED -> BOOTSTRAPPING -> REGISTERING -> VALIDATING -> INITIALIZING -> READY -> RUNNING

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Post-initialization application state.

        Raises:
            ApplicationBootstrapError: If validation or bootstrap step fails.
            InitializationError: If subsystem initialization fails.
        """
        with self._lock:
            if config:
                self._config = config

            logger.info("Initiating ApplicationRuntime lifecycle sequence...")

            # 1. BOOTSTRAPPING
            self._status = ApplicationLifecycleState.BOOTSTRAPPING
            logger.info("State transition -> BOOTSTRAPPING")

            # 2. REGISTERING
            self._status = ApplicationLifecycleState.REGISTERING
            logger.info("State transition -> REGISTERING")
            if self._runtime_registry.count() == 0:
                self._runtime_registry.register_runtime(
                    RuntimeRegistration(name="application_runtime", version=self._config.version)
                )

            # 3. VALIDATING
            self._status = ApplicationLifecycleState.VALIDATING
            logger.info("State transition -> VALIDATING")
            try:
                self._startup_validator.validate_startup(
                    self._config, registry=self._runtime_registry
                )
            except StartupValidationError as exc:
                self._status = ApplicationLifecycleState.FAILED
                logger.error("Lifecycle failed at VALIDATING stage: %s", exc)
                raise ApplicationBootstrapError(f"Validation failed: {exc}") from exc

            # 4. INITIALIZING
            self._status = ApplicationLifecycleState.INITIALIZING
            logger.info("State transition -> INITIALIZING")
            try:
                self._initialization_manager.initialize_all(self._context)
            except InitializationError as exc:
                self._status = ApplicationLifecycleState.FAILED
                logger.error("Lifecycle failed at INITIALIZING stage: %s", exc)
                raise

            # 5. READY
            self._status = ApplicationLifecycleState.READY
            logger.info("State transition -> READY")

            # 6. RUNNING
            self._status = ApplicationLifecycleState.RUNNING
            self._start_time = datetime.now(timezone.utc)
            logger.info("State transition -> RUNNING. ApplicationRuntime active.")

            return self.state()

    def start(self) -> ApplicationState:
        """Start the application runtime (IApplicationRuntime interface).

        Returns:
            ApplicationState: Updated state snapshot.
        """
        with self._lock:
            if self._status != ApplicationLifecycleState.RUNNING:
                return self.initialize()
            return self.state()

    def shutdown(self) -> ApplicationState:
        """Shutdown the application runtime completely and release all subsystem resources.

        Lifecycle sequence:
        RUNNING -> STOPPING -> STOPPED

        Returns:
            ApplicationState: Post-shutdown application state.
        """
        with self._lock:
            logger.info("Initiating ApplicationRuntime shutdown sequence...")
            self._status = ApplicationLifecycleState.STOPPING

            self._initialization_manager.shutdown_all()
            self._bootstrap_manager.shutdown()

            self._status = ApplicationLifecycleState.STOPPED
            logger.info("ApplicationRuntime shutdown complete. State transition -> STOPPED.")
            return self.state()

    def stop(self) -> ApplicationState:
        """Stop the application runtime safely (IApplicationRuntime interface).

        Returns:
            ApplicationState: Post-shutdown application state.
        """
        return self.shutdown()

    def restart(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Restart application runtime safely.

        Args:
            config: Optional configuration override.

        Returns:
            ApplicationState: Post-restart application state snapshot.
        """
        with self._lock:
            logger.info("Restarting ApplicationRuntime...")
            self._restart_count += 1
            self.shutdown()
            return self.initialize(config)

    def health(self) -> ApplicationHealth:
        """Get aggregate application health consolidated across all sub-managers.

        Returns:
            ApplicationHealth: Aggregated health assessment.
        """
        with self._lock:
            reg_health = self._runtime_registry.health()
            init_healthy = (
                len(self._initialization_manager.get_initialized_components()) > 0
                or self._status != ApplicationLifecycleState.RUNNING
            )

            subsystem_health: Dict[str, bool] = dict(reg_health.subsystem_health)
            subsystem_health["runtime_registry"] = reg_health.is_healthy
            subsystem_health["initialization_manager"] = init_healthy
            subsystem_health["bootstrap_manager"] = self._bootstrap_manager.boot_success

            issues = list(reg_health.issues)
            if self._status == ApplicationLifecycleState.FAILED:
                issues.append("ApplicationRuntime state is FAILED.")

            overall_healthy = (
                reg_health.is_healthy
                and self._status not in (ApplicationLifecycleState.FAILED, ApplicationLifecycleState.DEGRADED)
            )

            return ApplicationHealth(
                is_healthy=overall_healthy,
                state=self._status,
                subsystem_health=subsystem_health,
                issues=tuple(issues),
                checked_at=datetime.now(timezone.utc),
            )

    def get_health(self) -> ApplicationHealth:
        """Get current health assessment (IApplicationRuntime interface).

        Returns:
            ApplicationHealth: Aggregated health.
        """
        return self.health()

    def statistics(self) -> ApplicationStatistics:
        """Get aggregated application statistics metrics across all sub-managers.

        Returns:
            ApplicationStatistics: Aggregated runtime metrics.
        """
        with self._lock:
            uptime = 0.0
            if self._start_time and self._status == ApplicationLifecycleState.RUNNING:
                uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

            boot_stats = self._bootstrap_manager.collect_boot_statistics()

            metrics: Dict[str, float] = {}
            metrics.update(boot_stats.metrics)
            metrics.update(
                {
                    "boot_count": float(self._bootstrap_manager.boot_count),
                    "restart_count": float(self._restart_count + self._bootstrap_manager.restart_count),
                    "shutdown_count": float(self._initialization_manager.shutdown_count),
                    "registered_runtimes_count": float(self._runtime_registry.count()),
                    "failed_initializations": float(self._initialization_manager.failed_initializations),
                    "successful_initializations": float(self._initialization_manager.successful_initializations),
                    "rollback_count": float(self._initialization_manager.rollback_count),
                    "boot_duration_seconds": float(self._bootstrap_manager.boot_duration),
                    "uptime_seconds": float(uptime),
                }
            )

            return ApplicationStatistics(
                registered_runtimes_count=self._runtime_registry.count(),
                metrics=metrics,
            )

    def get_statistics(self) -> ApplicationStatistics:
        """Get current statistics (IApplicationRuntime interface).

        Returns:
            ApplicationStatistics: Aggregated statistics.
        """
        return self.statistics()

    def diagnostics(self) -> ApplicationDiagnostics:
        """Get system telemetry and diagnostics snapshot.

        Returns:
            ApplicationDiagnostics: System diagnostics.
        """
        with self._lock:
            messages = (
                f"Runtime status: {self._status.value}",
                f"Registered runtimes: {self._runtime_registry.count()}",
                f"Initialized components: {len(self._initialization_manager.get_initialized_components())}",
            )
            extra_info: Dict[str, Any] = {
                "app_name": self._config.app_name,
                "version": self._config.version,
                "status": self._status.value,
            }
            return ApplicationDiagnostics(
                timestamp=datetime.now(timezone.utc),
                diagnostic_messages=messages,
                extra_info=extra_info,
            )

    def get_diagnostics(self) -> ApplicationDiagnostics:
        """Get diagnostics (IApplicationRuntime interface).

        Returns:
            ApplicationDiagnostics: System diagnostics.
        """
        return self.diagnostics()

    def capabilities(self) -> ApplicationCapabilities:
        """Get application declared capability model.

        Returns:
            ApplicationCapabilities: Immutable capabilities.
        """
        return ApplicationCapabilities(
            voice_enabled=True,
            ai_reasoning_enabled=True,
            planning_enabled=True,
            os_automation_enabled=True,
            background_tasks_enabled=True,
            supports_restart=True,
            supports_bootstrap=True,
            supports_runtime_registration=True,
            supports_health_checks=True,
            supports_validation=True,
            supports_shutdown=True,
        )

    def get_capabilities(self) -> ApplicationCapabilities:
        """Get application capabilities (IApplicationRuntime interface).

        Returns:
            ApplicationCapabilities: Capability model.
        """
        return self.capabilities()

    def get_context(self) -> ApplicationContext:
        """Get current execution context.

        Returns:
            ApplicationContext: Execution context snapshot.
        """
        with self._lock:
            return self._context

    def register_runtime(self, registration: RuntimeRegistration) -> bool:
        """Register a subsystem runtime.

        Args:
            registration: Runtime registration metadata.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            return self._runtime_registry.register_runtime(registration)

    def lookup_runtime(self, name: str) -> Optional[RuntimeRegistration]:
        """Look up a registered subsystem runtime by name.

        Args:
            name: Subsystem name.

        Returns:
            Optional[RuntimeRegistration]: Registration record if found.
        """
        with self._lock:
            return self._runtime_registry.get_runtime(name)

    def clear(self) -> None:
        """Clear all registered runtimes."""
        with self._lock:
            self._runtime_registry.clear()
