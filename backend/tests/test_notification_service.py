"""Unit tests for NotificationService (Phase 11.5)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.desktop import (
    DesktopNotification,
    NotificationError,
    NotificationLevel,
    NotificationService,
)


def test_notification_service_send_and_history() -> None:
    svc = NotificationService()

    notif = svc.send_notification(
        title="Test Alert",
        message="This is a test notification",
        level=NotificationLevel.SUCCESS,
    )

    assert isinstance(notif, DesktopNotification)
    assert notif.title == "Test Alert"
    assert notif.level == NotificationLevel.SUCCESS

    history = svc.get_history()
    assert len(history) == 1
    assert history[0].notification_id == notif.notification_id

    svc.clear_history()
    assert len(svc.get_history()) == 0


def test_notification_service_empty_validation() -> None:
    svc = NotificationService()
    with pytest.raises(NotificationError):
        svc.send_notification(title="", message="")
