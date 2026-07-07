"""Coordinates voice states, sound alerts, and text notifications."""

from typing import Optional
from utils.logger import get_logger

from voice.ux.models import AssistantStatus
from voice.ux.status_manager import StatusManager
from voice.ux.sound_manager import SoundManager
from voice.ux.notification_manager import NotificationManager

logger = get_logger(__name__)


class FeedbackManager:
    """Facade coordinator unifying status tracking, sound chimes, and notifications."""

    def __init__(
        self,
        status_manager: Optional[StatusManager] = None,
        sound_manager: Optional[SoundManager] = None,
        notification_manager: Optional[NotificationManager] = None,
    ) -> None:
        """Initializes the FeedbackManager with sub-managers.

        Args:
            status_manager: Tracks current state. None instantiates default.
            sound_manager: Plays audio chimes. None instantiates default.
            notification_manager: Publishes text alerts. None instantiates default.
        """
        self.status_manager = status_manager or StatusManager()
        self.sound_manager = sound_manager or SoundManager()
        self.notification_manager = notification_manager or NotificationManager()

    def transition_to(
        self, status: AssistantStatus, custom_message: Optional[str] = None
    ) -> None:
        """Transitions the assistant state, triggers chimes, and publishes alerts.

        Args:
            status: The target AssistantStatus state.
            custom_message: Optional custom notification text message override.
        """
        logger.info("Feedback transitioning to: %s", status.name)

        # 1. Update active status (notifies status change listeners)
        self.status_manager.status = status

        # 2. Trigger audio alert chime (non-blocking)
        self.sound_manager.play_cue(status)

        # 3. Publish text notification (notifies pub-sub listeners)
        self.notification_manager.publish(status, custom_message=custom_message)
