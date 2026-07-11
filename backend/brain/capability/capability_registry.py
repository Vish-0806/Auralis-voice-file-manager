"""Capability registry maintaining brain-layer capability mappings for Auralis."""

from __future__ import annotations

import logging
from typing import Dict


class CapabilityRegistry:
    """Manages active and registered capabilities within the brain layer."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the CapabilityRegistry with default supported capabilities."""
        self._logger = logger or logging.getLogger(__name__)
        self._registry: Dict[str, str] = {}
        self._register_defaults()

    def register_capability(self, name: str, identifier: str) -> None:
        """Registers a new capability name mapping.

        Args:
            name: The user-friendly name (e.g. 'Browser', 'Developer').
            identifier: The system-level identifier (e.g. 'browser_cap', 'dev_cap').
        """
        self._registry[name.title()] = identifier
        self._logger.info(
            "Registered new capability in brain registry",
            extra={"name": name, "identifier": identifier},
        )

    def get_identifier(self, name: str) -> str | None:
        """Retrieves the system identifier for a given capability name."""
        return self._registry.get(name.title())

    def has_capability(self, name: str) -> bool:
        """Checks if a capability name is registered."""
        return name.title() in self._registry

    def list_capabilities(self) -> Dict[str, str]:
        """Returns all currently registered capability name mappings."""
        return self._registry.copy()

    def _register_defaults(self) -> None:
        """Registers default capabilities specified in the system design."""
        self.register_capability("File", "mock_file")
        self.register_capability("Desktop", "desktop")
        self.register_capability("Voice", "voice")
        self.register_capability("Workflow", "workflow")
