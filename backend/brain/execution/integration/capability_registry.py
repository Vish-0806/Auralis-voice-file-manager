"""Capability Registry for the Auralis Execution Runtime Integration (Phase 12.9).

Registers, enables, disables, and queries ExecutionCapability models for targets.
"""

import threading
from typing import Any, Dict, List, Optional

from brain.execution.integration.exceptions import CapabilityError
from brain.execution.integration.interfaces import ICapabilityRegistry
from brain.execution.integration.integration_models import ExecutionCapability, ExecutionTarget


class CapabilityRegistry(ICapabilityRegistry):
    """Thread-safe capability registry storing ExecutionCapability models."""

    def __init__(self) -> None:
        """Initializes CapabilityRegistry and registers default capabilities."""
        self._lock = threading.RLock()
        self._capabilities: Dict[str, ExecutionCapability] = {}
        self._register_default_capabilities()

    def _register_default_capabilities(self) -> None:
        """Registers default subsystem capabilities."""
        defaults = [
            ("Intent Recognition & Entity Extraction", ExecutionTarget.INTENT_ENGINE),
            ("Command Execution Orchestration", ExecutionTarget.COMMAND_ORCHESTRATOR),
            ("Multi-Step Workflow Scheduling", ExecutionTarget.WORKFLOW_ENGINE),
            ("Long-Running Task Management", ExecutionTarget.TASK_RUNTIME),
            ("Automation & Rule Scheduling", ExecutionTarget.AUTOMATION_RUNTIME),
        ]
        for name, target in defaults:
            self.register_capability(name=name, target=target, enabled=True)

    def register_capability(
        self,
        name: str,
        target: ExecutionTarget,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCapability:
        """Register a new execution capability.

        Args:
            name: Capability name string.
            target: ExecutionTarget enum.
            enabled: Boolean flag indicating if capability is enabled.
            metadata: Optional metadata dictionary.

        Returns:
            ExecutionCapability model.

        Raises:
            CapabilityError: If capability name is empty.
        """
        if not name:
            raise CapabilityError("Capability name cannot be empty")

        with self._lock:
            cap = ExecutionCapability(
                name=name,
                target=target,
                enabled=enabled,
                metadata=dict(metadata or {}),
            )
            self._capabilities[cap.capability_id] = cap
            return cap

    def get_capability(self, capability_id: str) -> Optional[ExecutionCapability]:
        """Fetch capability by capability_id."""
        with self._lock:
            return self._capabilities.get(capability_id)

    def list_capabilities(self, target: Optional[ExecutionTarget] = None) -> List[ExecutionCapability]:
        """List capabilities matching optional target filter.

        Args:
            target: Optional ExecutionTarget filter.

        Returns:
            List of ExecutionCapability objects.
        """
        with self._lock:
            if not target:
                return list(self._capabilities.values())
            return [c for c in self._capabilities.values() if c.target == target]

    def count_capabilities(self) -> int:
        """Return total registered capabilities count."""
        with self._lock:
            return len(self._capabilities)

    def clear(self) -> None:
        """Clear all registered capabilities."""
        with self._lock:
            self._capabilities.clear()
