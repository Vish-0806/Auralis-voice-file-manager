"""Brain Registry managing the lifecycle and registration of AI Brain modules for Auralis."""

from __future__ import annotations

import logging
from typing import Any, Dict


class BrainRegistry:
    """Dynamic registry managing active modules in the AI Brain Controller."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the BrainRegistry.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._modules: Dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        """Registers a subsystem module dynamically under a key name.

        Args:
            name: The key name identifying the module (e.g. 'GoalInterpreter').
            module: Concrete implementation class instance.
        """
        self._modules[name] = module
        self._logger.info("Subsystem module registered dynamically", extra={"module_name": name})

    def get_module(self, name: str) -> Any | None:
        """Retrieves a registered module by name."""
        return self._modules.get(name)

    def has_module(self, name: str) -> bool:
        """Checks if a module is registered."""
        return name in self._modules

    def list_modules(self) -> list[str]:
        """Returns list of registered module names."""
        return sorted(list(self._modules.keys()))
