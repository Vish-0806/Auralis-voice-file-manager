"""Initialization Manager (Phase 14.1).

Coordinates initialization order and readiness checks across registered subsystems.
"""

from threading import RLock
from typing import Optional, Tuple

from backend.application.interfaces import IInitializationManager, IRuntimeRegistry
from backend.application.models import ApplicationContext


class InitializationManager(IInitializationManager):
    """Manages subsystem initialization sequence and readiness checks."""

    def __init__(
        self, runtime_registry: Optional[IRuntimeRegistry] = None
    ) -> None:
        """Initialize InitializationManager with Constructor Dependency Injection.

        Args:
            runtime_registry: Optional runtime registry instance.
        """
        self._lock = RLock()
        self._runtime_registry = runtime_registry

    def initialize_all(self, context: ApplicationContext) -> bool:
        """Initialize all managed subsystems in dependency order.

        Args:
            context: Application context snapshot.

        Returns:
            bool: True if initialization succeeded for all subsystems.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError

    def is_initialized(self) -> bool:
        """Check if initialization has completed successfully.

        Returns:
            bool: True if initialized.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError

    def get_initialized_components(self) -> Tuple[str, ...]:
        """Get component names that have completed initialization.

        Returns:
            Tuple[str, ...]: Component names.

        Raises:
            NotImplementedError: Pending business logic implementation.
        """
        raise NotImplementedError
