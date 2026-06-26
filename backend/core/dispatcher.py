"""
Module: backend.core.dispatcher

Responsibility:
    Executes and dispatches planned actions to registered Capability modules.
    Enforces security permissions checking and logs events to the EventBus.

This module SHOULD:
    - Inject the IEventBus interface in its constructor to dispatch execution events.
    - Match actions against registered ICapability tool instances.
    - Publish runtime execution status events (success, failure, security blocks) to the EventBus.

This module should NEVER:
    - Interface with native OS libraries, terminal processes, or files directly.
    - Hardcode specific capability logic or directories.
    - Block asynchronous threads.
"""

from typing import Dict, Any, List, Callable, Optional
from core.interfaces import ICapability
from events.interfaces import IEventBus


class ExecutionResult:
    """Standardized return envelope for capability actions execution outcomes."""
    
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
    """Dispatches execution steps to registered capabilities and logs details to the EventBus."""
    
    def __init__(self, event_bus: IEventBus) -> None:
        self.event_bus: IEventBus = event_bus
        self.capabilities: Dict[str, ICapability] = {}
        self.security_guard: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def register_capability(self, capability: ICapability) -> None:
        """Registers a system capability by its name key."""
        pass

    def set_security_guard(self, guard: Callable[[str, Dict[str, Any]], bool]) -> None:
        """Configures the security validation guard callback."""
        pass

    def dispatch(self, capability_name: str, action: str, arguments: Dict[str, Any]) -> ExecutionResult:
        """Dispatches the action request after verifying permission boundaries and logs results."""
        pass
