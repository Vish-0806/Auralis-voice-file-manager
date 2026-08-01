"""Capability Registry implementation (Phase 11.9).

Provides thread-safe registration, lookup, and enumeration of all operating system
subsystem capabilities.
"""

import threading
from typing import Dict, List, Optional

from brain.os.integration.integration_models import (
    CapabilityDescriptor,
    OperationTarget,
)
from brain.os.integration.interfaces import ICapabilityRegistry


class CapabilityRegistry(ICapabilityRegistry):
    """Thread-safe capability registry for OS capabilities."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._registry: Dict[str, CapabilityDescriptor] = {}
        self._load_default_capabilities()

    def _load_default_capabilities(self) -> None:
        """Pre-load canonical capabilities for Phases 11.1-11.8."""
        defaults = [
            CapabilityDescriptor(
                capability_name="filesystem.open",
                target=OperationTarget.FILESYSTEM,
                description="Open or read filesystem path",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="filesystem.copy",
                target=OperationTarget.FILESYSTEM,
                description="Copy file or directory",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="filesystem.move",
                target=OperationTarget.FILESYSTEM,
                description="Move file or directory",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="filesystem.delete",
                target=OperationTarget.FILESYSTEM,
                description="Delete file or directory",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="application.launch",
                target=OperationTarget.APPLICATION,
                description="Launch desktop application",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="application.close",
                target=OperationTarget.APPLICATION,
                description="Close running application",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="process.kill",
                target=OperationTarget.PROCESS,
                description="Terminate running process",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="process.list",
                target=OperationTarget.PROCESS,
                description="List active OS processes",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="window.focus",
                target=OperationTarget.WINDOW,
                description="Focus target desktop window",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="window.minimize",
                target=OperationTarget.WINDOW,
                description="Minimize target window",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="desktop.notify",
                target=OperationTarget.DESKTOP,
                description="Display system desktop notification",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="device.volume",
                target=OperationTarget.DEVICE,
                description="Adjust audio device volume level",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="device.battery",
                target=OperationTarget.DEVICE,
                description="Inspect system power and battery status",
                is_enabled=True,
                requires_admin=False,
            ),
            CapabilityDescriptor(
                capability_name="security.evaluate",
                target=OperationTarget.SECURITY,
                description="Evaluate security request through security gateway",
                is_enabled=True,
                requires_admin=False,
            ),
        ]

        for desc in defaults:
            self.register(desc)

    def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a new OS capability."""
        with self._lock:
            self._registry[descriptor.capability_name] = descriptor

    def unregister(self, capability_name: str) -> bool:
        """Unregister an existing capability."""
        with self._lock:
            if capability_name in self._registry:
                del self._registry[capability_name]
                return True
            return False

    def lookup(self, capability_name: str) -> Optional[CapabilityDescriptor]:
        """Lookup capability descriptor by capability name."""
        with self._lock:
            return self._registry.get(capability_name)

    def get_capabilities(
        self, target: Optional[OperationTarget] = None
    ) -> List[CapabilityDescriptor]:
        """List all registered capabilities or filter by target category."""
        with self._lock:
            if target is None:
                return list(self._registry.values())
            return [cap for cap in self._registry.values() if cap.target == target]

    def list_categories(self) -> List[OperationTarget]:
        """List all operation target categories with registered capabilities."""
        with self._lock:
            cats = {cap.target for cap in self._registry.values()}
            return list(cats)
