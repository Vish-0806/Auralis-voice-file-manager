"""Runtime Registry (Phase 14.1).

Provides thread-safe registration, resolution, and inspection of sub-system runtimes
across the application lifecycle.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, Optional, Tuple

from backend.application.exceptions import RuntimeRegistrationError
from backend.application.interfaces import IRuntimeRegistry
from backend.application.models import (
    ApplicationHealth,
    ApplicationLifecycleState,
    ApplicationStatistics,
    RuntimeRegistration,
)

logger = logging.getLogger(__name__)


class RuntimeRegistry(IRuntimeRegistry):
    """Thread-safe registry for managing subsystem runtime registrations."""

    def __init__(self) -> None:
        """Initialize RuntimeRegistry with lock protection and internal storage."""
        self._lock = RLock()
        self._registrations: Dict[str, RuntimeRegistration] = {}

    def register_runtime(self, registration: RuntimeRegistration) -> bool:
        """Register a subsystem runtime.

        Args:
            registration: Subsystem runtime registration metadata.

        Returns:
            bool: True if registration succeeded.

        Raises:
            RuntimeRegistrationError: If a runtime with the same name is already registered.
        """
        with self._lock:
            if registration.name in self._registrations:
                raise RuntimeRegistrationError(
                    f"Runtime with name '{registration.name}' is already registered."
                )
            self._registrations[registration.name] = registration
            logger.info("Registered subsystem runtime: %s", registration.name)
            return True

    def register(self, registration: RuntimeRegistration) -> bool:
        """Register a subsystem runtime (IRuntimeRegistry alias).

        Args:
            registration: Subsystem runtime registration metadata.

        Returns:
            bool: True if registration succeeded.

        Raises:
            RuntimeRegistrationError: If a runtime with the same name is already registered.
        """
        return self.register_runtime(registration)

    def unregister_runtime(self, name: str) -> bool:
        """Unregister a subsystem runtime by name.

        Args:
            name: Name of the target subsystem runtime.

        Returns:
            bool: True if unregistration succeeded, False if not found.
        """
        with self._lock:
            if name not in self._registrations:
                logger.warning("Attempted to unregister non-existent runtime: %s", name)
                return False
            del self._registrations[name]
            logger.info("Unregistered subsystem runtime: %s", name)
            return True

    def unregister(self, name: str) -> bool:
        """Unregister a subsystem runtime by name (IRuntimeRegistry alias).

        Args:
            name: Name of the target subsystem runtime.

        Returns:
            bool: True if unregistration succeeded, False if not found.
        """
        return self.unregister_runtime(name)

    def get_runtime(self, name: str) -> Optional[RuntimeRegistration]:
        """Retrieve registration record for a subsystem by name.

        Args:
            name: Name of the subsystem runtime.

        Returns:
            Optional[RuntimeRegistration]: Registration record if present.
        """
        with self._lock:
            return self._registrations.get(name)

    def get_registration(self, name: str) -> Optional[RuntimeRegistration]:
        """Retrieve registration record for a subsystem by name (IRuntimeRegistry alias).

        Args:
            name: Name of the subsystem runtime.

        Returns:
            Optional[RuntimeRegistration]: Registration record if present.
        """
        return self.get_runtime(name)

    def contains_runtime(self, name: str) -> bool:
        """Check if a subsystem runtime is registered by name.

        Args:
            name: Name of the subsystem runtime.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            return name in self._registrations

    def is_registered(self, name: str = "") -> bool:
        """Check if a subsystem runtime is registered by name (IRuntimeRegistry alias).

        Args:
            name: Name of the subsystem runtime.

        Returns:
            bool: True if registered.
        """
        return self.contains_runtime(name)

    def list_runtimes(self) -> Tuple[RuntimeRegistration, ...]:
        """List all active subsystem runtime registrations in registration order.

        Returns:
            Tuple[RuntimeRegistration, ...]: Tuple of active registrations.
        """
        with self._lock:
            return tuple(self._registrations.values())

    def list_registrations(self) -> Tuple[RuntimeRegistration, ...]:
        """List all active subsystem runtime registrations (IRuntimeRegistry alias).

        Returns:
            Tuple[RuntimeRegistration, ...]: Tuple of active registrations.
        """
        return self.list_runtimes()

    def count(self) -> int:
        """Get the total count of registered runtimes.

        Returns:
            int: Number of registered runtimes.
        """
        with self._lock:
            return len(self._registrations)

    def clear(self) -> None:
        """Clear all registered subsystem runtimes."""
        with self._lock:
            self._registrations.clear()
            logger.info("Cleared all subsystem runtime registrations.")

    def health(self) -> ApplicationHealth:
        """Get aggregate health assessment of registered runtimes.

        Returns:
            ApplicationHealth: Aggregated health information.
        """
        with self._lock:
            subsystem_health = {
                name: reg.is_active for name, reg in self._registrations.items()
            }
            all_healthy = all(subsystem_health.values()) if subsystem_health else True
            issues = tuple(
                f"Runtime '{name}' is inactive."
                for name, is_active in subsystem_health.items()
                if not is_active
            )
            return ApplicationHealth(
                is_healthy=all_healthy,
                state=(
                    ApplicationLifecycleState.RUNNING
                    if all_healthy
                    else ApplicationLifecycleState.DEGRADED
                ),
                subsystem_health=subsystem_health,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ApplicationStatistics:
        """Get runtime registry statistics.

        Returns:
            ApplicationStatistics: Registry statistics metrics.
        """
        with self._lock:
            active_count = sum(
                1 for reg in self._registrations.values() if reg.is_active
            )
            return ApplicationStatistics(
                registered_runtimes_count=len(self._registrations),
                metrics={
                    "total_registered": float(len(self._registrations)),
                    "active_registered": float(active_count),
                },
            )
