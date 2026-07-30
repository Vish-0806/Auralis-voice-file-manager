"""Dependency Registry for the Auralis Brain Runtime (Phase 9.7).

Thread-safe registry responsible for managing, validating, and resolving subsystem runtimes.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Union

from brain.runtime.brain_models import RuntimeComponent

logger = logging.getLogger(__name__)


class DependencyRegistry:
    """Thread-safe registry for subsystem runtimes in the Auralis Brain architecture.

    Responsibilities:
    - Register subsystem runtimes.
    - Resolve dependencies by component type.
    - Validate subsystem registrations.
    - Auto-discover default runtimes when not explicitly registered.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._registry: Dict[str, Any] = {}
        logger.debug("DependencyRegistry initialized")

    def register(self, component: Union[RuntimeComponent, str], instance: Any) -> None:
        """Register a subsystem runtime instance.

        Args:
            component: RuntimeComponent enum or component name string.
            instance: The subsystem runtime instance.
        """
        name = self._normalize_name(component)
        with self._lock:
            self._registry[name] = instance
            logger.info("Dependency Registered: component=%s instance=%s", name, type(instance).__name__)

    def get(self, component: Union[RuntimeComponent, str]) -> Optional[Any]:
        """Resolve a subsystem runtime instance.

        Auto-discovers via default global singleton getter if not explicitly registered.

        Args:
            component: RuntimeComponent enum or component name string.

        Returns:
            Subsystem instance or None.
        """
        name = self._normalize_name(component)
        with self._lock:
            if name in self._registry:
                instance = self._registry[name]
                logger.debug("Dependency Resolved: component=%s", name)
                return instance

            # Auto-discovery fallback
            instance = self._auto_discover(name)
            if instance is not None:
                self._registry[name] = instance
                logger.info("Dependency Registered (auto-discovered): component=%s", name)
                return instance

            logger.warning("Dependency Resolution Failed: component=%s not found", name)
            return None

    def unregister(self, component: Union[RuntimeComponent, str]) -> bool:
        """Remove a registered subsystem runtime.

        Args:
            component: Component to unregister.

        Returns:
            True if removed, False if not found.
        """
        name = self._normalize_name(component)
        with self._lock:
            if name in self._registry:
                del self._registry[name]
                logger.info("Dependency Unregistered: component=%s", name)
                return True
            return False

    def validate_registrations(self) -> Dict[str, bool]:
        """Validate all expected subsystem registrations.

        Returns:
            Dict mapping component names to availability boolean.
        """
        with self._lock:
            expected = [c.value for c in RuntimeComponent if c != RuntimeComponent.BRAIN]
            result = {}
            for comp in expected:
                instance = self.get(comp)
                result[comp] = instance is not None
            return result

    def resolve_all(self) -> Dict[str, Any]:
        """Resolve all registered/discoverable subsystem runtimes.

        Returns:
            Dict mapping component names to runtime instances.
        """
        with self._lock:
            expected = [c.value for c in RuntimeComponent if c != RuntimeComponent.BRAIN]
            resolved = {}
            for comp in expected:
                inst = self.get(comp)
                if inst is not None:
                    resolved[comp] = inst
            return resolved

    def list_components(self) -> List[str]:
        """List all currently registered component names.

        Returns:
            List of component name strings.
        """
        with self._lock:
            return list(self._registry.keys())

    def clear(self) -> None:
        """Clear all registered dependencies."""
        with self._lock:
            self._registry.clear()
            logger.debug("DependencyRegistry cleared")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _normalize_name(self, component: Union[RuntimeComponent, str]) -> str:
        if isinstance(component, RuntimeComponent):
            return component.value
        return str(component).upper()

    def _auto_discover(self, name: str) -> Optional[Any]:
        """Attempt to resolve default subsystem runtime singletons."""
        try:
            if name == RuntimeComponent.VOICE.value:
                from brain.voice.runtime import get_voice_runtime
                return get_voice_runtime()
            elif name == RuntimeComponent.CONVERSATION.value:
                from brain.conversation.runtime import get_conversation_runtime
                return get_conversation_runtime()
            elif name == RuntimeComponent.REASONING.value:
                from brain.reasoning.runtime import get_reasoning_runtime
                return get_reasoning_runtime()
            elif name == RuntimeComponent.PLANNING.value:
                from brain.planning.runtime import get_planning_runtime
                return get_planning_runtime()
            elif name == RuntimeComponent.EXECUTION.value:
                from brain.execution.runtime import get_execution_runtime
                return get_execution_runtime()
            elif name == RuntimeComponent.FILESYSTEM.value:
                from brain.filesystem.runtime import get_filesystem_runtime
                return get_filesystem_runtime()
        except Exception as exc:
            logger.warning("Auto-discovery failed for %s: %s", name, exc)
        return None
