"""
Module: backend.core.interfaces

Responsibility:
    Defines abstract interface contracts for Auralis system components.
    Enables Dependency Inversion by decoupling Core logic from implementation details of
    the AI Brain, Memory systems, OS adapters, and specific Capabilities.

This module SHOULD:
    - Declare abstract classes (using abc.ABC) and Protocols representing system boundaries.
    - Standardize parameters and return types across all subsystems.
    - Provide a stable contract for plugins, adapters, and engines.

This module should NEVER:
    - Include concrete execution logic or implementations of databases, OS functions, or models.
    - Import external libraries like fastapi, sqlite3, or pyaudio.
    - Reference specific runtime classes or variables.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IOSAdapter(ABC):
    """Abstract port defining OS Abstraction Layer operations."""
    
    @abstractmethod
    def execute_shell(self, command: str) -> str:
        """Executes a system shell command and returns stdout."""
        pass

    @abstractmethod
    def resolve_path(self, path: str) -> str:
        """Resolves relative or environment paths into absolute system paths."""
        pass


class ICapability(ABC):
    """Abstract contract for modular assistant capability extensions."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the registration name of the capability."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns a description of capabilities and tools."""
        pass

    @abstractmethod
    def execute(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a capability action with the given arguments."""
        pass


class IMemoryEngine(ABC):
    """Abstract contract for tiered memory storage systems."""
    
    @abstractmethod
    def retrieve_context(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Retrieves semantically similar context objects."""
        pass

    @abstractmethod
    def save_context(self, item: Dict[str, Any]) -> None:
        """Saves a conversational or environmental context to memory."""
        pass


class IAgentBrain(ABC):
    """Abstract contract for reasoning models and intent parsers."""
    
    @abstractmethod
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the reasoning loop to determine execution steps."""
        pass
