"""
Module: backend.core.state

Responsibility:
    Defines thread-safe state containers and transition rules.
    Exposes state observation APIs to notify system listeners of status updates.

This module SHOULD:
    - Define a SystemState enum or class identifying valid operational phases.
    - Provide a SystemStateManager class that manages transitions thread-safely.
    - Implement an Observer interface for dispatching state update signals.

This module should NEVER:
    - Bind updates directly to UI react hooks or HTML views.
    - Block system threads during status update dispatches.
    - Hardcode business logic actions inside state transition events.
"""

from typing import List, Callable, Dict, Any, Optional
import enum
import threading


class SystemStatus(enum.Enum):
    """Supported execution status phases of Auralis."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    ERROR = "error"


class SystemStateManager:
    """Tracks and modifies system-wide execution states thread-safely."""
    
    def __init__(self) -> None:
        self._current_status: SystemStatus = SystemStatus.IDLE
        self._lock: threading.Lock = threading.Lock()
        self._observers: List[Callable[[SystemStatus, SystemStatus], None]] = []

    def get_status(self) -> SystemStatus:
        """Returns the current system status phase."""
        with self._lock:
            return self._current_status

    def transition_to(self, new_status: SystemStatus) -> None:
        """Transitions the system state to a new phase and triggers observer alerts."""
        pass

    def register_observer(self, callback: Callable[[SystemStatus, SystemStatus], None]) -> None:
        """Registers a callback to be triggered when the status changes."""
        pass
