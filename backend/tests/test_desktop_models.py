"""Unit tests for Phase 11.5 Desktop Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.desktop import (
    ClipboardContent,
    ClipboardFormat,
    DesktopCapabilities,
    DesktopEnvironment,
    DesktopHealth,
    DesktopInfo,
    DesktopNotification,
    DesktopRuntimeStatus,
    DesktopStatistics,
    KnownFolder,
    KnownFolderType,
    NotificationLevel,
)


def test_desktop_enums() -> None:
    assert DesktopEnvironment.WINDOWS.value == "windows"
    assert ClipboardFormat.TEXT.value == "text"
    assert NotificationLevel.INFO.value == "info"
    assert KnownFolderType.DESKTOP.value == "desktop"


def test_known_folder_defaults_and_immutability() -> None:
    folder = KnownFolder(folder_type=KnownFolderType.DOCUMENTS, name="Documents", path="/path/to/docs")
    assert folder.folder_type == KnownFolderType.DOCUMENTS
    assert folder.path == "/path/to/docs"

    with pytest.raises((TypeError, ValidationError)):
        folder.path = "/other"  # type: ignore


def test_desktop_info_defaults_and_immutability() -> None:
    info = DesktopInfo(environment=DesktopEnvironment.WINDOWS, user_name="User")
    assert info.environment == DesktopEnvironment.WINDOWS
    assert info.user_name == "User"

    with pytest.raises((TypeError, ValidationError)):
        info.user_name = "Other"  # type: ignore


def test_desktop_notification_defaults_and_immutability() -> None:
    notif = DesktopNotification(notification_id="123", title="Test", message="Body")
    assert notif.notification_id == "123"
    assert notif.level == NotificationLevel.INFO

    with pytest.raises((TypeError, ValidationError)):
        notif.title = "New"  # type: ignore


def test_clipboard_content_defaults_and_immutability() -> None:
    content = ClipboardContent(format=ClipboardFormat.TEXT, text_content="hello")
    assert content.format == ClipboardFormat.TEXT
    assert content.text_content == "hello"

    with pytest.raises((TypeError, ValidationError)):
        content.text_content = "world"  # type: ignore
