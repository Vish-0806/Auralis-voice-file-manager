"""
Module: backend.capabilities.models

Responsibility:
    Provides structured data models representing capability schemas and results.

Future Expansion:
    Support dynamic serialization mapping for remote network protocols.
"""

from typing import Dict, Any, List, Optional
import time


class ToolActionDefinition:
    """Represents the structural description of a capability tool action."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.parameters: Dict[str, Any] = parameters


class ActionResult:
    """Wrapper representing the outcome of a capability action."""
    
    def __init__(self,
                 success: bool,
                 output: Dict[str, Any],
                 error_message: Optional[str] = None) -> None:
        self.success: bool = success
        self.output: Dict[str, Any] = output
        self.error_message: Optional[str] = error_message
        self.timestamp: float = time.time()
