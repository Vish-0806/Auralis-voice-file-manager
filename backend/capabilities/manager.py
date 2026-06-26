"""
Module: backend.capabilities.manager

Responsibility:
    Orchestrates the loading, discovery, and setup lifecycle of capabilities.

Future Expansion:
    Scanning third-party plugin paths to load custom capability packages.
"""

from capabilities.interfaces import ICapabilityManager, ICapabilityRegistry


class CapabilityManager(ICapabilityManager):
    """Manages capability lifecycles and registers discovered tools."""
    
    def __init__(self, registry: ICapabilityRegistry) -> None:
        self.registry: ICapabilityRegistry = registry

    def load_capabilities(self) -> None:
        """Scans configured capability sub-packages and registers them."""
        pass
