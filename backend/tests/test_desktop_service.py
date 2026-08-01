"""Unit tests for DesktopService (Phase 11.5)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.desktop import DesktopInfo, DesktopService, KnownFolder, KnownFolderType


def test_desktop_service_get_known_folders() -> None:
    svc = DesktopService()
    folders = svc.get_known_folders()
    assert isinstance(folders, dict)
    assert KnownFolderType.HOME in folders
    assert KnownFolderType.DESKTOP in folders

    home_folder = folders[KnownFolderType.HOME]
    assert isinstance(home_folder, KnownFolder)
    assert home_folder.exists is True

    desktop_folder = svc.get_known_folder(KnownFolderType.DESKTOP)
    assert desktop_folder is not None
    assert desktop_folder.folder_type == KnownFolderType.DESKTOP


def test_desktop_service_get_desktop_info() -> None:
    svc = DesktopService()
    info = svc.get_desktop_info()
    assert isinstance(info, DesktopInfo)
    assert len(info.user_name) > 0
    assert len(info.known_folders) > 0
