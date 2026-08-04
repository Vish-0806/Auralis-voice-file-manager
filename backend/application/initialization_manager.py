"""Initialization Manager (Phase 14.1).

Coordinates multi-subsystem initialization and shutdown in deterministic order,
supporting safe rollbacks, custom component initializers, and statistics tracking.
"""

import logging
from threading import RLock
from typing import Callable, Dict, List, Optional, Tuple

from backend.application.exceptions import InitializationError
from backend.application.interfaces import IInitializationManager, IRuntimeRegistry
from backend.application.models import ApplicationContext

logger = logging.getLogger(__name__)

# Standard deterministic initialization sequence across subsystems
DETERMINISTIC_INITIALIZATION_ORDER: Tuple[str, ...] = (
    "brain_runtime",
    "ai_runtime",
    "os_runtime",
    "execution_runtime",
    "assistant_runtime",
    "api_runtime",
    "voice_runtime",
    "application_runtime",
)


class InitializationManager(IInitializationManager):
    """Manages subsystem initialization sequence, shutdown sequence, and rollback handling."""

    def __init__(
        self, runtime_registry: Optional[IRuntimeRegistry] = None
    ) -> None:
        """Initialize InitializationManager with Constructor Dependency Injection.

        Args:
            runtime_registry: Optional runtime registry instance.
        """
        self._lock = RLock()
        self._runtime_registry = runtime_registry
        self._initialized_components: List[str] = []
        self._initializers: Dict[str, Callable[[], bool]] = {}
        self._shutdown_handlers: Dict[str, Callable[[], bool]] = {}

        # Statistics
        self.successful_initializations: int = 0
        self.failed_initializations: int = 0
        self.rollback_count: int = 0
        self.shutdown_count: int = 0
        self.restart_count: int = 0

    def register_initializer(
        self,
        name: str,
        init_fn: Callable[[], bool],
        shutdown_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        """Register custom initialization and shutdown handlers for a component.

        Args:
            name: Component runtime name.
            init_fn: Zero-arg callable returning bool indicating success.
            shutdown_fn: Optional zero-arg callable returning bool for shutdown.
        """
        with self._lock:
            self._initializers[name] = init_fn
            if shutdown_fn:
                self._shutdown_handlers[name] = shutdown_fn

    def initialize_all(self, context: Optional[ApplicationContext] = None) -> bool:
        """Initialize all managed subsystems in deterministic dependency order.

        Args:
            context: Optional application context snapshot.

        Returns:
            bool: True if initialization succeeded for all subsystems.

        Raises:
            InitializationError: If any subsystem initialization fails.
        """
        with self._lock:
            logger.info("Starting subsystem initialization sequence...")
            for comp_name in DETERMINISTIC_INITIALIZATION_ORDER:
                if comp_name in self._initialized_components:
                    continue

                try:
                    logger.info("Initializing subsystem: %s", comp_name)
                    success = True
                    if comp_name in self._initializers:
                        success = self._initializers[comp_name]()

                    if not success:
                        raise InitializationError(
                            f"Initializer for '{comp_name}' returned False."
                        )

                    self._initialized_components.append(comp_name)
                except Exception as exc:
                    self.failed_initializations += 1
                    logger.error(
                        "Initialization failed at '%s': %s. Triggering rollback...",
                        comp_name,
                        exc,
                    )
                    self.rollback_initialization()
                    raise InitializationError(
                        f"Subsystem initialization failed at '{comp_name}': {exc}"
                    ) from exc

            self.successful_initializations += 1
            logger.info(
                "Successfully initialized all %d subsystems.",
                len(self._initialized_components),
            )
            return True

    def rollback_initialization(self) -> bool:
        """Rollback already initialized subsystems in exact reverse order.

        Returns:
            bool: True if rollback completed.
        """
        with self._lock:
            logger.warning("Executing initialization rollback...")
            self.rollback_count += 1
            to_rollback = list(reversed(self._initialized_components))
            for comp_name in to_rollback:
                logger.info("Rolling back subsystem: %s", comp_name)
                if comp_name in self._shutdown_handlers:
                    try:
                        self._shutdown_handlers[comp_name]()
                    except Exception as exc:
                        logger.error("Error during rollback of '%s': %s", comp_name, exc)

            self._initialized_components.clear()
            return True

    def shutdown_all(self) -> bool:
        """Shutdown all initialized subsystems in exact reverse order.

        Returns:
            bool: True if shutdown succeeded for all components.
        """
        with self._lock:
            logger.info("Shutting down all subsystems in reverse order...")
            self.shutdown_count += 1
            to_shutdown = list(reversed(self._initialized_components))
            for comp_name in to_shutdown:
                logger.info("Shutting down subsystem: %s", comp_name)
                if comp_name in self._shutdown_handlers:
                    try:
                        self._shutdown_handlers[comp_name]()
                    except Exception as exc:
                        logger.error("Error shutting down '%s': %s", comp_name, exc)

            self._initialized_components.clear()
            logger.info("Completed subsystem shutdown.")
            return True

    def restart_all(self, context: Optional[ApplicationContext] = None) -> bool:
        """Restart all subsystems (shutdown followed by initialization).

        Args:
            context: Optional application context snapshot.

        Returns:
            bool: True if restart succeeded.
        """
        with self._lock:
            logger.info("Restarting all subsystems...")
            self.restart_count += 1
            self.shutdown_all()
            return self.initialize_all(context)

    def is_initialized(self) -> bool:
        """Check if all standard subsystems have completed initialization.

        Returns:
            bool: True if all subsystems are initialized.
        """
        with self._lock:
            return len(self._initialized_components) == len(
                DETERMINISTIC_INITIALIZATION_ORDER
            )

    def get_initialized_components(self) -> Tuple[str, ...]:
        """Get component names that have completed initialization.

        Returns:
            Tuple[str, ...]: Immutable tuple of initialized component names.
        """
        with self._lock:
            return tuple(self._initialized_components)
