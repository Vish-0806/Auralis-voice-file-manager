"""
Module: backend.os.interfaces

Responsibility:
    Defines abstract interface contracts for platform adapters and ports.

Future Expansion:
    Dynamic loading of OSAL adapter plugins for specialized environments.
"""

from abc import ABC, abstractmethod


class IOSPlatformAdapter(ABC):
    """Abstract base class representing an OS-specific adapter bundle."""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the name of the operating system platform."""
        pass

    @abstractmethod
    def validate_platform(self) -> bool:
        """Verifies if the current host matches this platform adapter."""
        pass
