"""Unit tests for WindowService (Phase 11.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.window import (
    WindowBounds,
    WindowInfo,
    WindowNotFoundError,
    WindowService,
    WindowState,
)


def test_window_service_inspect_window() -> None:
    svc = WindowService()
    # Discover any active window
    active_win = svc._detector.enumerate_windows()[0]

    win = svc.get_window(active_win.window_id)
    assert isinstance(win, WindowInfo)
    assert win.window_id == active_win.window_id

    bounds = svc.get_window_bounds(active_win.window_id)
    assert isinstance(bounds, WindowBounds)

    state = svc.get_window_state(active_win.window_id)
    assert isinstance(state, WindowState)


def test_window_service_invalid_target() -> None:
    svc = WindowService()
    with pytest.raises(WindowNotFoundError):
        svc.get_window("non_existent_window_id_99999")
