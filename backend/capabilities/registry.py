"""
Module: backend.capabilities.registry

Responsibility:
    Tracks registered capabilities in a thread-safe registry.

Future Expansion:
    Dynamic capability reloading without server restarts.
"""

from typing import Dict, Any, List, Optional
import threading
from capabilities.interfaces import ICapabilityRegistry, ICapability


class CapabilityRegistry(ICapabilityRegistry):
    """Thread-safe registry indexing all active system capabilities."""
    
    def __init__(self) -> None:
        self._capabilities: Dict[str, ICapability] = {}
        self._lock: threading.Lock = threading.Lock()

    def register(self, capability: ICapability) -> None:
        """Adds a capability instance to the registry."""
        pass

    def get_capability(self, name: str) -> Optional[ICapability]:
        """Retrieves a registered capability by its name key."""
        pass

    def list_capabilities(self) -> List[ICapability]:
        """Returns all active capabilities registered in the system."""
        pass
