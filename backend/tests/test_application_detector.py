"""Unit tests for ApplicationDetector (Phase 11.3)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.application import ApplicationDetector, InstalledApplication


def test_application_detector_find_executable() -> None:
    detector = ApplicationDetector()

    # Common system binary that exists on all platforms
    python_exe = detector.find_executable("python")
    assert python_exe is not None
    assert isinstance(python_exe, str)

    is_inst = detector.is_installed("python")
    assert is_inst is True


def test_application_detector_discover() -> None:
    detector = ApplicationDetector()
    apps = detector.detect_installed_applications()
    assert isinstance(apps, list)
    assert len(apps) > 0

    app_names = [a.info.name.lower() for a in apps]
    assert any("python" in n for n in app_names)
