"""
Module: backend.core.context

Responsibility:
    Defines the SystemContext data models and builder patterns.
    Aggregates environmental variables, active workspaces, and system performance metrics.

This module SHOULD:
    - Declare a SystemContext class containing typed properties for system environments.
    - Provide a ContextBuilder class that aggregates inputs from OS adapters.
    - Support serialization methods (e.g., dict conversions) to format contexts for prompts.

This module should NEVER:
    - Interface directly with host DLLs, windows processes, or shell inputs.
    - Hardcode platform-specific metrics fetch loops.
    - Modify system configurations or states.
"""

from typing import Dict, Any, List, Optional
from backend.core.interfaces import IOSAdapter


class SystemContext:
    """Represents the collected active environment state of the host operating system."""
    
    def __init__(self,
                 active_directory: str,
                 active_window: str,
                 cpu_usage: float,
                 ram_usage: float,
                 user_profile: str,
                 system_time: str,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        self.active_directory: str = active_directory
        self.active_window: str = active_window
        self.cpu_usage: float = cpu_usage
        self.ram_usage: float = ram_usage
        self.user_profile: str = user_profile
        self.system_time: str = system_time
        self.metadata: Dict[str, Any] = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the context state into a flat dictionary."""
        return {
            "active_directory": self.active_directory,
            "active_window": self.active_window,
            "cpu_usage": self.cpu_usage,
            "ram_usage": self.ram_usage,
            "user_profile": self.user_profile,
            "system_time": self.system_time,
            "metadata": self.metadata
        }


class ContextBuilder:
    """Constructs SystemContext states dynamically using OS adapters."""
    
    def __init__(self, os_adapter: IOSAdapter) -> None:
        self.os_adapter: IOSAdapter = os_adapter

    def build_current_context(self) -> SystemContext:
        """Queries OS adapters to assemble the current system state context."""
        # Query active paths and metrics from the adapter
        pass
