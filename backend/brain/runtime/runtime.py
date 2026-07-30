"""Brain Runtime Coordinator for the Auralis Backend (Phase 9.7).

Provides singleton lifecycle management, global accessors, and health/statistics entry points for the Brain Runtime.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
import uuid
from typing import List, Optional, Union

from brain.runtime.assistant_runtime import AssistantRuntime
from brain.runtime.brain_controller import BrainController
from brain.runtime.brain_models import (
    BrainRequest,
    BrainResponse,
    BrainRuntimeHealth,
    BrainRuntimeStatistics,
)

logger = logging.getLogger(__name__)


class BrainRuntimeStatus(str, Enum):
    """Lifecycle status states for the Brain Runtime Coordinator."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    PROCESSING = "PROCESSING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class BrainRuntimeCoordinator:
    """Thread-safe singleton coordinator for the central Auralis Brain Runtime.

    Responsibilities:
    - Hold and manage the singleton BrainController instance.
    - Provide thread-safe initialization, request processing, health monitoring, and shutdown.
    """

    def __init__(self, controller: Optional[BrainController] = None) -> None:
        self._lock = threading.RLock()
        self._controller = controller
        self._status = BrainRuntimeStatus.INITIALIZING
        self._runtime_id = f"brain-rt-{uuid.uuid4().hex[:6]}"
        logger.debug("BrainRuntimeCoordinator created runtime_id=%s", self._runtime_id)

    def initialize(self) -> bool:
        """Initialize the Brain Runtime and all underlying subsystem runtimes.

        Returns:
            True if initialization succeeded.
        """
        with self._lock:
            try:
                self._status = BrainRuntimeStatus.INITIALIZING
                if self._controller is None:
                    self._controller = BrainController()
                ok = self._controller.initialize()
                self._status = BrainRuntimeStatus.READY if ok else BrainRuntimeStatus.ERROR
                logger.info("Brain Runtime Coordinator Initialized: runtime_id=%s status=%s", self._runtime_id, self._status)
                return ok
            except Exception as exc:
                self._status = BrainRuntimeStatus.ERROR
                logger.error("BrainRuntimeCoordinator.initialize failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Shutdown the Brain Runtime and all subsystem runtimes.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            self._status = BrainRuntimeStatus.SHUTDOWN
            if self._controller:
                self._controller.shutdown()
                self._controller = None
            logger.info("Brain Runtime Coordinator Shutdown: runtime_id=%s", self._runtime_id)
            return True

    def restart(self) -> bool:
        """Restart the complete Brain Runtime.

        Returns:
            True if re-initialization succeeded.
        """
        with self._lock:
            logger.info("Brain Runtime Coordinator Restarting: runtime_id=%s", self._runtime_id)
            self.shutdown()
            return self.initialize()

    def process_request(self, request: Union[BrainRequest, str]) -> BrainResponse:
        """Process a request through the complete Brain pipeline.

        Args:
            request: :class:`BrainRequest` or raw prompt string.

        Returns:
            Immutable :class:`BrainResponse`.
        """
        with self._lock:
            controller = self._get_controller()
            return controller.process_request(request)

    def health_check(self) -> BrainRuntimeHealth:
        """Check overall health status across all backend subsystems.

        Returns:
            Immutable :class:`BrainRuntimeHealth` snapshot.
        """
        with self._lock:
            controller = self._get_controller()
            return controller.health_check()

    def get_statistics(self) -> BrainRuntimeStatistics:
        """Fetch aggregated diagnostic statistics across all backend subsystems.

        Returns:
            Immutable :class:`BrainRuntimeStatistics` snapshot.
        """
        with self._lock:
            controller = self._get_controller()
            return controller.get_statistics()

    def list_components(self) -> List[str]:
        """List all registered subsystem component names.

        Returns:
            List of component name strings.
        """
        with self._lock:
            controller = self._get_controller()
            return controller.list_components()

    def clear(self) -> None:
        """Clear runtime state and statistics."""
        with self._lock:
            if self._controller:
                self._controller.clear()
            self._status = BrainRuntimeStatus.READY

    @property
    def status(self) -> BrainRuntimeStatus:
        with self._lock:
            return self._status

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_controller(self) -> BrainController:
        if self._controller is None or self._status == BrainRuntimeStatus.SHUTDOWN:
            self.initialize()
        if self._controller is None:
            raise RuntimeError("BrainRuntimeCoordinator: BrainController unavailable")
        return self._controller


# ---------------------------------------------------------------------------
# Global Singleton Accessors
# ---------------------------------------------------------------------------

_global_brain_runtime: Optional[BrainRuntimeCoordinator] = None
_global_brain_lock = threading.RLock()


def get_brain_runtime() -> BrainRuntimeCoordinator:
    """Return (or create) the global Brain Runtime singleton.

    Thread-safe. Automatically initializes if it does not exist.

    Returns:
        :class:`BrainRuntimeCoordinator` singleton instance.
    """
    global _global_brain_runtime
    with _global_brain_lock:
        if _global_brain_runtime is None:
            _global_brain_runtime = BrainRuntimeCoordinator()
            _global_brain_runtime.initialize()
        return _global_brain_runtime


def reset_brain_runtime() -> None:
    """Reset the global Brain Runtime singleton.

    Thread-safe. Next call to ``get_brain_runtime()`` creates a fresh instance.
    """
    global _global_brain_runtime
    with _global_brain_lock:
        if _global_brain_runtime is not None:
            try:
                _global_brain_runtime.shutdown()
            except Exception:
                pass
            _global_brain_runtime = None
        logger.debug("Brain Runtime reset")
