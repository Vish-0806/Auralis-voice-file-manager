"""Lifecycle Manager for the Auralis Brain Runtime (Phase 9.7).

Manages the ordered startup, shutdown, restart, and clear operations across all subsystem runtimes.
"""

import logging
import threading
from typing import Dict, List, Optional

from brain.runtime.brain_models import RuntimeComponent
from brain.runtime.dependency_registry import DependencyRegistry

logger = logging.getLogger(__name__)

# Strict startup order (bottom layer to top layer)
_STARTUP_ORDER: List[RuntimeComponent] = [
    RuntimeComponent.FILESYSTEM,
    RuntimeComponent.EXECUTION,
    RuntimeComponent.PLANNING,
    RuntimeComponent.REASONING,
    RuntimeComponent.CONVERSATION,
    RuntimeComponent.VOICE,
]

# Shutdown order is LIFO (top layer to bottom layer)
_SHUTDOWN_ORDER: List[RuntimeComponent] = list(reversed(_STARTUP_ORDER))


class LifecycleManager:
    """Thread-safe lifecycle coordinator for the Auralis Brain architecture.

    Responsibilities:
    - Ordered initialization of all subsystem runtimes.
    - Ordered (LIFO) graceful shutdown of all subsystem runtimes.
    - Full system restart and clear operations.
    """

    def __init__(self, registry: Optional[DependencyRegistry] = None) -> None:
        self._lock = threading.RLock()
        self._registry = registry or DependencyRegistry()
        self._status: Dict[str, str] = {c.value: "UNINITIALIZED" for c in _STARTUP_ORDER}
        logger.debug("LifecycleManager initialized")

    def initialize_all(self) -> bool:
        """Initialize all subsystem runtimes in strict dependency order.

        Returns:
            True if all subsystems initialized successfully, False on any failure.
        """
        with self._lock:
            all_ok = True
            for comp in _STARTUP_ORDER:
                name = comp.value
                instance = self._registry.get(comp)
                if instance is None:
                    logger.error("LifecycleManager: Cannot initialize %s — instance not found", name)
                    self._status[name] = "ERROR"
                    all_ok = False
                    continue

                try:
                    if hasattr(instance, "initialize") and callable(instance.initialize):
                        ok = instance.initialize()
                        if ok is not False:
                            self._status[name] = "READY"
                            logger.info("Subsystem Initialized: component=%s", name)
                        else:
                            self._status[name] = "ERROR"
                            logger.error("Subsystem Initialization Failed: component=%s", name)
                            all_ok = False
                    else:
                        # Non-coordinator instance or duck-typed
                        self._status[name] = "READY"
                        logger.info("Subsystem Initialized (implicit): component=%s", name)
                except Exception as exc:
                    self._status[name] = "ERROR"
                    logger.error("Subsystem Initialization Exception: component=%s error=%s", name, exc)
                    all_ok = False

            return all_ok

    def shutdown_all(self) -> bool:
        """Shutdown all subsystem runtimes in LIFO order.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            all_ok = True
            for comp in _SHUTDOWN_ORDER:
                name = comp.value
                instance = self._registry.get(comp)
                if instance is None:
                    self._status[name] = "SHUTDOWN"
                    continue

                try:
                    if hasattr(instance, "shutdown") and callable(instance.shutdown):
                        instance.shutdown()
                    self._status[name] = "SHUTDOWN"
                    logger.info("Subsystem Shutdown: component=%s", name)
                except Exception as exc:
                    self._status[name] = "SHUTDOWN"
                    logger.error("Subsystem Shutdown Exception: component=%s error=%s", name, exc)
                    all_ok = False

            return all_ok

    def restart_all(self) -> bool:
        """Shutdown all subsystems LIFO, then re-initialize in startup order.

        Returns:
            True if re-initialization succeeded.
        """
        with self._lock:
            logger.info("LifecycleManager: Restarting all subsystems")
            self.shutdown_all()
            return self.initialize_all()

    def clear_all(self) -> None:
        """Clear all subsystem state/statistics where supported."""
        with self._lock:
            for comp in _STARTUP_ORDER:
                instance = self._registry.get(comp)
                if instance and hasattr(instance, "clear") and callable(instance.clear):
                    try:
                        instance.clear()
                    except Exception as exc:
                        logger.warning("LifecycleManager clear failed for %s: %s", comp.value, exc)
            self._registry.clear()
            self._status = {c.value: "UNINITIALIZED" for c in _STARTUP_ORDER}
            logger.debug("LifecycleManager cleared")

    def get_status(self) -> Dict[str, str]:
        """Return snapshot of current subsystem lifecycle states.

        Returns:
            Dict mapping component names to status strings.
        """
        with self._lock:
            return dict(self._status)
