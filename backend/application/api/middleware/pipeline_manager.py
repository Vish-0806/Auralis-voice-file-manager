"""API Middleware Pipeline Manager Implementation (Phase 15.3).

Thread-safe pipeline manager constructing ordered, immutable middleware sequences
for each execution stage (before-request, around-request, after-request, error-handler).
"""

import logging
from threading import RLock
from typing import Optional, Tuple

from backend.application.api.middleware.interfaces import (
    IMiddlewareRegistry,
    IPipelineManager,
)
from backend.application.api.middleware.middleware_registry import (
    MiddlewareRegistry,
)
from backend.application.api.middleware.models import (
    ApiMiddleware,
    MiddlewareStage,
    MiddlewareState,
)

logger = logging.getLogger(__name__)


class PipelineManager(IPipelineManager):
    """Thread-safe pipeline builder assembling ordered ENABLED middleware sequences."""

    def __init__(self, registry: Optional[IMiddlewareRegistry] = None) -> None:
        """Initialize PipelineManager using Constructor Dependency Injection.

        Args:
            registry: Optional IMiddlewareRegistry implementation instance.
        """
        self._lock = RLock()
        self._registry = registry or MiddlewareRegistry()

    def build_before_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for BEFORE_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered ENABLED middlewares.
        """
        return self.build_pipeline(MiddlewareStage.BEFORE_REQUEST)

    def build_around_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for AROUND_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered ENABLED middlewares.
        """
        return self.build_pipeline(MiddlewareStage.AROUND_REQUEST)

    def build_after_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for AFTER_REQUEST stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered ENABLED middlewares.
        """
        return self.build_pipeline(MiddlewareStage.AFTER_REQUEST)

    def build_error_pipeline(self) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline for ERROR_HANDLER stage.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered ENABLED middlewares.
        """
        return self.build_pipeline(MiddlewareStage.ERROR_HANDLER)

    def build_pipeline(self, stage: MiddlewareStage) -> Tuple[ApiMiddleware, ...]:
        """Build priority-ordered pipeline of ENABLED middlewares for a specific stage.

        Args:
            stage: Target MiddlewareStage enum.

        Returns:
            Tuple[ApiMiddleware, ...]: Ordered tuple of enabled middlewares.
        """
        with self._lock:
            middlewares = self._registry.list_middlewares(stage=stage)
            enabled = [m for m in middlewares if m.state == MiddlewareState.ENABLED]
            # Sorted by priority ascending (lower numbers = higher execution priority)
            enabled.sort(key=lambda m: (m.priority, m.middleware_id))
            logger.debug("Built pipeline for stage '%s' with %d middlewares.", stage.value, len(enabled))
            return tuple(enabled)
