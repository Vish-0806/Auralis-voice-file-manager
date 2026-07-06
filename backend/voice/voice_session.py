"""
Auralis Voice Session Manager
Handles session telemetry and bridges state actions for voice workflows.
"""

import time
import uuid
from typing import Any, Dict, Optional
from voice.interfaces import IVoiceSessionManager
from voice.models import VoiceSession


class VoiceSessionManager(IVoiceSessionManager):
    """Manages transaction status and bridges pending actions to app state."""

    def __init__(self) -> None:
        self.session = VoiceSession(
            session_id=str(uuid.uuid4()),
            is_active=True,
            last_active_time=time.time()
        )

    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Bridges retrieval of pending action state from the application's core manager."""
        from capabilities.files.file_operations import get_pending_action
        return get_pending_action()

    def set_pending_action(self, action: str, target: str, destination: Optional[str] = None) -> None:
        """Saves a pending state action."""
        from app.confirmation_manager import ConfirmationManager
        ConfirmationManager.set_pending_action(action, target, destination)
        self.session.last_active_time = time.time()

    def clear_pending_action(self) -> None:
        """Clears out currently stored pending state actions."""
        from app.confirmation_manager import ConfirmationManager
        ConfirmationManager.clear_pending_action()
        self.session.last_active_time = time.time()
