"""Brain Controller for the Auralis Brain Runtime (Phase 9.7).

The single public entry-point facade for the entire Auralis backend runtime.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Union

from brain.runtime.assistant_runtime import AssistantRuntime
from brain.runtime.brain_models import (
    BrainRequest,
    BrainResponse,
    BrainRuntimeHealth,
    BrainRuntimeStatistics,
)

logger = logging.getLogger(__name__)


class BrainController:
    """Single public entry-point controller for the Auralis backend architecture.

    Responsibilities:
    - Expose unified API facade (`initialize`, `shutdown`, `restart`, `process_request`,
      `health_check`, `get_statistics`, `list_components`, `clear`).
    - Delegate all operations to the underlying AssistantRuntime.
    - Thread-safe via RLock.
    """

    def __init__(self, assistant_runtime: Optional[AssistantRuntime] = None) -> None:
        self._lock = threading.RLock()
        self._assistant = assistant_runtime or AssistantRuntime()
        logger.debug("BrainController initialized")

    def initialize(self) -> bool:
        """Initialize the complete Auralis backend runtime.

        Returns:
            True if all subsystems initialized cleanly.
        """
        with self._lock:
            return self._assistant.initialize()

    def shutdown(self) -> bool:
        """Shutdown the complete Auralis backend runtime.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            return self._assistant.shutdown()

    def restart(self) -> bool:
        """Restart all subsystem runtimes in the Auralis backend.

        Returns:
            True if re-initialization succeeded.
        """
        with self._lock:
            return self._assistant.restart()

    def process_request(self, request: Union[BrainRequest, str]) -> BrainResponse:
        """Process an incoming voice/text request through the complete brain pipeline.

        Args:
            request: :class:`BrainRequest` object or raw user prompt string.

        Returns:
            Immutable :class:`BrainResponse`.
        """
        with self._lock:
            return self._assistant.process_request(request)

    def health_check(self) -> BrainRuntimeHealth:
        """Check overall health status across all backend subsystems.

        Returns:
            Immutable :class:`BrainRuntimeHealth` snapshot.
        """
        with self._lock:
            return self._assistant.health_check()

    def get_statistics(self) -> BrainRuntimeStatistics:
        """Fetch aggregated diagnostic statistics across all backend subsystems.

        Returns:
            Immutable :class:`BrainRuntimeStatistics` snapshot.
        """
        with self._lock:
            return self._assistant.get_statistics()

    def list_components(self) -> List[str]:
        """List all currently registered subsystem components.

        Returns:
            List of component name strings.
        """
        with self._lock:
            return self._assistant.list_components()

    def clear(self) -> None:
        """Clear all backend runtime state and statistics."""
        with self._lock:
            self._assistant.clear()
