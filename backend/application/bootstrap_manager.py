"""Bootstrap Manager (Phase 14.1).

Manages the application bootstrap phase lifecycle, coordinating startup validation,
subsystem initialization, timing metrics, and runtime registration.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Optional

from backend.application.exceptions import ApplicationBootstrapError
from backend.application.interfaces import (
    IBootstrapManager,
    IInitializationManager,
    IRuntimeRegistry,
    IStartupValidator,
)
from backend.application.models import (
    ApplicationConfiguration,
    ApplicationLifecycleState,
    ApplicationState,
    ApplicationStatistics,
)

logger = logging.getLogger(__name__)


class BootstrapManager(IBootstrapManager):
    """Coordinates application bootstrapping, component setup, and boot lifecycle stats."""

    def __init__(
        self,
        initialization_manager: Optional[IInitializationManager] = None,
        startup_validator: Optional[IStartupValidator] = None,
        runtime_registry: Optional[IRuntimeRegistry] = None,
    ) -> None:
        """Initialize BootstrapManager with Constructor Dependency Injection.

        Args:
            initialization_manager: Optional initialization manager instance.
            startup_validator: Optional startup validator instance.
            runtime_registry: Optional runtime registry instance.
        """
        self._lock = RLock()
        self._initialization_manager = initialization_manager
        self._startup_validator = startup_validator
        self._runtime_registry = runtime_registry

        # Boot Lifecycle State
        self._boot_state: ApplicationState = ApplicationState(
            status=ApplicationLifecycleState.UNINITIALIZED
        )
        self.boot_start_time: Optional[datetime] = None
        self.boot_end_time: Optional[datetime] = None
        self.boot_duration: float = 0.0
        self.boot_success: bool = False
        self.boot_failures: int = 0
        self.boot_count: int = 0
        self.restart_count: int = 0

    def boot(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Boot all application components and subsystems safely.

        Args:
            config: Optional application configuration settings.

        Returns:
            ApplicationState: Post-boot application state snapshot.

        Raises:
            ApplicationBootstrapError: If validation or initialization fails during boot.
        """
        with self._lock:
            self.boot_count += 1
            self.boot_start_time = datetime.now(timezone.utc)
            self._boot_state = ApplicationState(
                status=ApplicationLifecycleState.INITIALIZING,
                start_time=self.boot_start_time,
            )
            logger.info("Starting application boot sequence (boot_count=%d)...", self.boot_count)

            cfg = config or ApplicationConfiguration()

            # Step 1: Startup Validation
            if self._startup_validator is not None:
                try:
                    self._startup_validator.validate_startup(
                        config=cfg, registry=self._runtime_registry
                    )
                except Exception as exc:
                    self.boot_failures += 1
                    self.boot_success = False
                    self._boot_state = ApplicationState(
                        status=ApplicationLifecycleState.FAILED,
                        is_healthy=False,
                        metadata={"error": str(exc)},
                    )
                    logger.error("Boot failed during validation phase: %s", exc)
                    raise ApplicationBootstrapError(
                        f"Application boot failed during validation: {exc}"
                    ) from exc

            # Step 2: Subsystem Initialization
            if self._initialization_manager is not None:
                try:
                    self._initialization_manager.initialize_all()
                except Exception as exc:
                    self.boot_failures += 1
                    self.boot_success = False
                    self._boot_state = ApplicationState(
                        status=ApplicationLifecycleState.FAILED,
                        is_healthy=False,
                        metadata={"error": str(exc)},
                    )
                    logger.error("Boot failed during subsystem initialization phase: %s", exc)
                    raise ApplicationBootstrapError(
                        f"Application boot failed during initialization: {exc}"
                    ) from exc

            # Step 3: Complete Boot Timing
            self.boot_end_time = datetime.now(timezone.utc)
            if self.boot_start_time:
                self.boot_duration = (
                    self.boot_end_time - self.boot_start_time
                ).total_seconds()

            self.boot_success = True
            self._boot_state = ApplicationState(
                status=ApplicationLifecycleState.RUNNING,
                is_active=True,
                is_healthy=True,
                start_time=self.boot_start_time,
                uptime_seconds=self.boot_duration,
            )
            logger.info(
                "Application boot completed successfully in %.4f seconds.",
                self.boot_duration,
            )
            return self._boot_state

    def bootstrap(self, config: ApplicationConfiguration) -> ApplicationState:
        """Bootstrap all application components and subsystems (IBootstrapManager interface).

        Args:
            config: Application configuration.

        Returns:
            ApplicationState: Post-bootstrap state.
        """
        return self.boot(config)

    def restart(
        self, config: Optional[ApplicationConfiguration] = None
    ) -> ApplicationState:
        """Restart application runtime by shutting down and re-booting.

        Args:
            config: Optional application configuration settings.

        Returns:
            ApplicationState: Post-restart application state snapshot.
        """
        with self._lock:
            logger.info("Restarting application via BootstrapManager...")
            self.restart_count += 1
            self.shutdown()
            return self.boot(config)

    def shutdown(self) -> ApplicationState:
        """Shutdown bootstrapped components and release allocated resources.

        Returns:
            ApplicationState: Post-shutdown application state snapshot.
        """
        with self._lock:
            logger.info("Shutting down application via BootstrapManager...")
            if self._initialization_manager is not None:
                self._initialization_manager.shutdown_all()

            self._boot_state = ApplicationState(
                status=ApplicationLifecycleState.SHUTDOWN,
                is_active=False,
                is_healthy=True,
            )
            return self._boot_state

    def teardown(self) -> ApplicationState:
        """Teardown bootstrapped components (IBootstrapManager interface).

        Returns:
            ApplicationState: Post-teardown state.
        """
        return self.shutdown()

    def is_bootstrapped(self) -> bool:
        """Check if bootstrapping was completed successfully.

        Returns:
            bool: True if bootstrapped and running.
        """
        with self._lock:
            return (
                self.boot_success
                and self._boot_state.status == ApplicationLifecycleState.RUNNING
            )

    def get_bootstrap_state(self) -> ApplicationState:
        """Get current bootstrap state snapshot.

        Returns:
            ApplicationState: Bootstrap state snapshot.
        """
        with self._lock:
            return self._boot_state

    def collect_boot_statistics(self) -> ApplicationStatistics:
        """Collect and return boot statistics and timing metrics.

        Returns:
            ApplicationStatistics: Boot timing and operational metrics.
        """
        with self._lock:
            return ApplicationStatistics(
                metrics={
                    "boot_duration_seconds": float(self.boot_duration),
                    "boot_failures": float(self.boot_failures),
                    "boot_count": float(self.boot_count),
                    "restart_count": float(self.restart_count),
                    "boot_success": 1.0 if self.boot_success else 0.0,
                }
            )
