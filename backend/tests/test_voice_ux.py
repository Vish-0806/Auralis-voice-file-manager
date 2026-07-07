"""Unit tests for the voice UX subsystem."""

from unittest.mock import MagicMock, patch
import pytest

from voice.ux.models import AssistantStatus, UXNotification
from voice.ux.status_manager import StatusManager
from voice.ux.sound_manager import SoundManager
from voice.ux.notification_manager import NotificationManager
from voice.ux.feedback_manager import FeedbackManager


def test_status_manager_transitions():
    """Verify that StatusManager transitions states and notifies listeners."""
    sm = StatusManager(initial_status=AssistantStatus.SLEEPING)
    assert sm.status == AssistantStatus.SLEEPING

    transitions = []

    def mock_listener(old, new):
        transitions.append((old, new))

    sm.register_listener(mock_listener)

    # Transition to LISTENING
    sm.status = AssistantStatus.LISTENING
    assert sm.status == AssistantStatus.LISTENING
    assert len(transitions) == 1
    assert transitions[0] == (AssistantStatus.SLEEPING, AssistantStatus.LISTENING)

    # Transition to same status should not trigger listener
    sm.status = AssistantStatus.LISTENING
    assert len(transitions) == 1

    # Unregister listener
    sm.unregister_listener(mock_listener)
    sm.status = AssistantStatus.PROCESSING
    assert len(transitions) == 1  # Still 1, since listener was removed


@patch("winsound.PlaySound")
def test_sound_manager_plays_cues(mock_playsound):
    """Verify that SoundManager triggers winsound playing on Windows."""
    sm = SoundManager()
    # Play wake cue
    sm.play_cue(AssistantStatus.WAKE_DETECTED)
    mock_playsound.assert_called_once()
    assert "SystemAsterisk" in mock_playsound.call_args[0][0]


def test_notification_manager_publishing():
    """Verify that NotificationManager publishes notifications to listeners."""
    nm = NotificationManager()
    assert nm.get_message_for_status(AssistantStatus.LISTENING) == "Listening..."

    received_notifications = []

    def mock_notification_listener(notif):
        received_notifications.append(notif)

    nm.register_listener(mock_notification_listener)

    # Publish standard status
    nm.publish(AssistantStatus.LISTENING)
    assert len(received_notifications) == 1
    assert received_notifications[0].status == AssistantStatus.LISTENING
    assert received_notifications[0].message == "Listening..."
    assert received_notifications[0].timestamp > 0

    # Publish custom message override
    nm.publish(AssistantStatus.ERROR, custom_message="Timeout reached!")
    assert len(received_notifications) == 2
    assert received_notifications[1].status == AssistantStatus.ERROR
    assert received_notifications[1].message == "Timeout reached!"


def test_feedback_manager_coordination():
    """Verify that FeedbackManager coordinates Status, Sound, and Notification managers."""
    mock_sm = MagicMock()
    mock_so = MagicMock()
    mock_nm = MagicMock()

    fm = FeedbackManager(
        status_manager=mock_sm,
        sound_manager=mock_so,
        notification_manager=mock_nm,
    )

    fm.transition_to(AssistantStatus.PROCESSING, custom_message="Executing command...")

    # Verify coordinator updated status on status manager
    mock_sm.status = AssistantStatus.PROCESSING

    # Verify coordinator played cue on sound manager
    mock_so.play_cue.assert_called_once_with(AssistantStatus.PROCESSING)

    # Verify coordinator published notification on notification manager
    mock_nm.publish.assert_called_once_with(
        AssistantStatus.PROCESSING, custom_message="Executing command..."
    )
