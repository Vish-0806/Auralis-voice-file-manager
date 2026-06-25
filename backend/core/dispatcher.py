"""
Module: backend.core.dispatcher

Responsibility:
    Executes and dispatches structured actions to target Capability modules.
    Enforces permission checking policies and confirmation checkpoints.

This module SHOULD:
    - Define an ActionDispatcher class that routes commands based on capability registries.
    - Declare an ExecutionResult wrapper structure containing status flags, outputs, and tracebacks.
    - Integrate check callbacks for security validation steps.

This module should NEVER:
    - Execute shell operations or OS system commands directly.
    - Hardcode specific capability logic (e.g. file copying or folder sorting).
    - Hardcode API endpoints.
"""

from typing import Dict, Any, List, Callable, Optional
from backend.core.interfaces import ICapability


class ExecutionResult:
    """Standardized return structure for capability execution actions."""
    
    def __init__(self,
                 success: bool,
                 output: Dict[str, Any],
                 error_message: Optional[str] = None,
                 execution_time: float = 0.0) -> None:
        self.success: bool = success
        self.output: Dict[str, Any] = output
        self.error_message: Optional[str] = error_message
        self.execution_time: float = execution_time


class ActionDispatcher:
    """Routes execution actions to registered Capability components."""
    
    def __init__(self) -> None:
        self.capabilities: Dict[str, ICapability] = {}
        self.security_guard: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def register_capability(self, capability: ICapability) -> None:
        """Indexes a Capability instance by its registration key."""
        pass

    def set_security_guard(self, guard: Callable[[str, Dict[str, Any]], bool]) -> None:
        """Sets a security validation callback interface."""
        pass

    def dispatch(self, capability_name: str, action: str, arguments: Dict[str, Any]) -> ExecutionResult:
        """Dispatches an action request to the target capability after running safety checks."""
        pass
