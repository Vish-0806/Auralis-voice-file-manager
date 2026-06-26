"""
Module: backend.capabilities.interfaces

Responsibility:
    Defines abstract interfaces for Auralis system capabilities.
    Establishes boundaries for registering, loading, and executing tools.

Future Expansion:
    Support for remote/gRPC capabilities or sandboxed plugin actions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from capabilities.models import ToolActionDefinition, ActionResult


class ICapability(ABC):
    """Abstract base class for all system capabilities."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the registration name of the capability."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns the description of capability tools."""
        pass

    @abstractmethod
    def get_actions(self) -> List[ToolActionDefinition]:
        """Returns the list of actions supported by this capability."""
        pass

    @abstractmethod
    def execute(self, action: str, arguments: Dict[str, Any]) -> ActionResult:
        """Executes a capability action with the given arguments."""
        pass


class ICapabilityRegistry(ABC):
    """Abstract base class for registering and matching capabilities."""
    
    @abstractmethod
    def register(self, capability: ICapability) -> None:
        """Registers a capability instance into the registry."""
        pass

    @abstractmethod
    def get_capability(self, name: str) -> Optional[ICapability]:
        """Retrieves a registered capability by its name key."""
        pass

    @abstractmethod
    def list_capabilities(self) -> List[ICapability]:
        """Returns all active capabilities registered in the system."""
        pass


class ICapabilityManager(ABC):
    """Abstract base class for managing capability lifecycles."""
    
    @abstractmethod
    def load_capabilities(self) -> None:
        """Loads and initializes all capabilities from the configured packages."""
        pass
