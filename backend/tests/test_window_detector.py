"""Unit tests for WindowDetector (Phase 11.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.window import WindowDetector, WindowInfo


def test_window_detector_enumerate_and_lookup() -> None:
    detector = WindowDetector()
    wins = detector.enumerate_windows()
    assert isinstance(wins, list)
    assert len(wins) > 0

    first = wins[0]
    found_id = detector.get_by_id(first.window_id)
    assert found_id is not None
    assert found_id.window_id == first.window_id

    by_title = detector.get_by_title(first.title)
    assert len(by_title) > 0

    active = detector.get_active_window()
    assert active is not None
