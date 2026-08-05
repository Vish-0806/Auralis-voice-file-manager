"""API Middleware Registry Implementation (Phase 15.3).

Thread-safe in-memory registry for managing API middlewares, supporting registration,
unregistration, enable/disable state toggling, priority ordering, duplicate detection,
and registration telemetry.
"""

import logging
from threading import RLock
from typing import Dict, Optional, Tuple

from backend.application.api.middleware.exceptions import (
    DuplicateMiddlewareException,
)
from backend.application.api.middleware.interfaces import IMiddlewareRegistry
from backend.application.api.middleware.models import (
    ApiMiddleware,
    MiddlewareStage,
    MiddlewareState,
)

logger = logging.getLogger(__name__)


class MiddlewareRegistry(IMiddlewareRegistry):
    """Thread-safe registry managing API middleware instances."""

    def __init__(self) -> None:
        """Initialize MiddlewareRegistry using Constructor Dependency Injection."""
        self._lock = RLock()
        self._middlewares: Dict[str, ApiMiddleware] = {}

        # Telemetry counters
        self._total_registrations = 0
        self._total_unregistrations = 0
        self._total_enables = 0
        self._total_disables = 0
        self._total_clears = 0

    def register(self, middleware: ApiMiddleware) -> ApiMiddleware:
        """Register a new middleware component in the registry.

        Args:
            middleware: Immutable ApiMiddleware instance.

        Returns:
            ApiMiddleware: Registered middleware instance.

        Raises:
            DuplicateMiddlewareException: If middleware_id is already registered.
        """
        with self._lock:
            if middleware.middleware_id in self._middlewares:
                raise DuplicateMiddlewareException(
                    f"Middleware with ID '{middleware.middleware_id}' is already registered."
                )

            self._middlewares[middleware.middleware_id] = middleware
            self._total_registrations += 1
            logger.info(
                "Registered middleware ID '%s' (%s) for stage '%s' with priority %d.",
                middleware.middleware_id,
                middleware.name,
                middleware.stage.value,
                middleware.priority,
            )
            return middleware

    def unregister(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Unregister a middleware component by ID.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Unregistered middleware if present, else None.
        """
        with self._lock:
            middleware = self._middlewares.pop(middleware_id, None)
            if middleware is not None:
                self._total_unregistrations += 1
                logger.info("Unregistered middleware ID '%s'.", middleware_id)
            return middleware

    def enable(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Enable a registered middleware component.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Updated ApiMiddleware if found, else None.
        """
        with self._lock:
            middleware = self._middlewares.get(middleware_id)
            if middleware is None:
                return None

            if middleware.state == MiddlewareState.ENABLED:
                return middleware

            updated = middleware.model_copy(update={"state": MiddlewareState.ENABLED})
            self._middlewares[middleware_id] = updated
            self._total_enables += 1
            logger.info("Enabled middleware ID '%s'.", middleware_id)
            return updated

    def disable(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Disable a registered middleware component.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Updated ApiMiddleware if found, else None.
        """
        with self._lock:
            middleware = self._middlewares.get(middleware_id)
            if middleware is None:
                return None

            if middleware.state == MiddlewareState.DISABLED:
                return middleware

            updated = middleware.model_copy(update={"state": MiddlewareState.DISABLED})
            self._middlewares[middleware_id] = updated
            self._total_disables += 1
            logger.info("Disabled middleware ID '%s'.", middleware_id)
            return updated

    def contains(self, middleware_id: str) -> bool:
        """Check if a middleware ID is registered.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            bool: True if present, False otherwise.
        """
        with self._lock:
            return middleware_id in self._middlewares

    def lookup(self, middleware_id: str) -> Optional[ApiMiddleware]:
        """Look up a middleware by ID.

        Args:
            middleware_id: Unique middleware identifier.

        Returns:
            Optional[ApiMiddleware]: Middleware instance if found, else None.
        """
        with self._lock:
            return self._middlewares.get(middleware_id)

    def list_middlewares(
        self, stage: Optional[MiddlewareStage] = None
    ) -> Tuple[ApiMiddleware, ...]:
        """List registered middlewares, optionally filtered by stage and sorted by priority ascending.

        Args:
            stage: Optional stage filter.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered tuple of matching middlewares.
        """
        with self._lock:
            filtered = list(self._middlewares.values())
            if stage is not None:
                filtered = [m for m in filtered if m.stage == stage]

            # Priority ordering: lower priority numbers executed first
            filtered.sort(key=lambda m: (m.priority, m.middleware_id))
            return tuple(filtered)

    def count(self) -> int:
        """Get total count of registered middlewares.

        Returns:
            int: Number of registered middlewares.
        """
        with self._lock:
            return len(self._middlewares)

    def clear(self) -> None:
        """Clear all registered middlewares from the registry."""
        with self._lock:
            self._middlewares.clear()
            self._total_clears += 1
            logger.info("MiddlewareRegistry cleared.")

    def get_telemetry_counters(self) -> Dict[str, int]:
        """Get internal telemetry counters under lock."""
        with self._lock:
            enabled_count = sum(
                1 for m in self._middlewares.values() if m.state == MiddlewareState.ENABLED
            )
            disabled_count = sum(
                1 for m in self._middlewares.values() if m.state == MiddlewareState.DISABLED
            )
            return {
                "total_registrations": self._total_registrations,
                "total_unregistrations": self._total_unregistrations,
                "total_enables": self._total_enables,
                "total_disables": self._total_disables,
                "total_clears": self._total_clears,
                "current_total": len(self._middlewares),
                "enabled_count": enabled_count,
                "disabled_count": disabled_count,
            }
