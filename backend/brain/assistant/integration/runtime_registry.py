"""Runtime Registry implementation for Auralis (Phase 13.9).

Registers, looks up, verifies dependencies, and exposes capability snapshots of assistant and system runtimes.
No mutable singleton globals. Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.integration.exceptions import AssistantValidationException
from brain.assistant.integration.interfaces import IRuntimeRegistry
from brain.assistant.integration.models import AssistantRuntimeSnapshot

logger = logging.getLogger(__name__)


class RuntimeRegistry(IRuntimeRegistry):
    """Thread-safe registry managing sub-runtime instances, capabilities, and availability."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._runtimes: Dict[str, Any] = {}
        self._versions: Dict[str, str] = {}
        self._capabilities: Dict[str, List[str]] = {}

    def register_runtime(
        self,
        name: str,
        runtime_instance: Any,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """Register a sub-runtime instance with version and capabilities metadata."""
        if not name or runtime_instance is None:
            raise AssistantValidationException("Runtime name and instance cannot be empty")

        with self._lock:
            self._runtimes[name] = runtime_instance
            self._versions[name] = version
            self._capabilities[name] = capabilities or ["default"]
            logger.info("Registered runtime name='%s' version='%s'", name, version)

    def get_runtime(self, name: str) -> Optional[Any]:
        """Lookup a registered sub-runtime by name."""
        with self._lock:
            return self._runtimes.get(name)

    def is_available(self, name: str) -> bool:
        """Check if a runtime is registered and available."""
        with self._lock:
            inst = self._runtimes.get(name)
            if inst is None:
                return False

            if hasattr(inst, "is_initialized"):
                return bool(getattr(inst, "is_initialized"))
            return True

    def list_snapshots(self) -> List[AssistantRuntimeSnapshot]:
        """List snapshots of all registered runtimes."""
        with self._lock:
            snapshots: List[AssistantRuntimeSnapshot] = []

            for name, inst in self._runtimes.items():
                version = self._versions.get(name, "1.0.0")
                caps = self._capabilities.get(name, [])
                avail = self.is_available(name)

                status_str = "READY" if avail else "UNAVAILABLE"
                if hasattr(inst, "get_health"):
                    try:
                        health = inst.get_health()
                        if hasattr(health, "status"):
                            status_str = getattr(health, "status")
                    except Exception as exc:
                        logger.debug("Error checking health for %s: %s", name, exc)

                snapshots.append(
                    AssistantRuntimeSnapshot(
                        runtime_name=name,
                        version=version,
                        is_available=avail,
                        status=status_str,
                        capabilities=caps,
                        metadata={"type": type(inst).__name__},
                    )
                )

            return snapshots

    def clear(self) -> None:
        """Clear all registered runtimes."""
        with self._lock:
            self._runtimes.clear()
            self._versions.clear()
            self._capabilities.clear()
