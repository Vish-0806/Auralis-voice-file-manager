"""Unit tests for Phase 11.6 Window Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.window import (
    WindowBounds,
    WindowCapabilities,
    WindowFocusState,
    WindowHealth,
    WindowInfo,
    WindowOperation,
    WindowOperationRequest,
    WindowOperationResult,
    WindowRuntimeStatus,
    WindowState,
    WindowStatistics,
    WindowType,
    WindowVisibility,
)


def test_window_enums() -> None:
    assert WindowVisibility.VISIBLE.value == "visible"
    assert WindowOperation.FOCUS.value == "focus"
    assert WindowType.NORMAL.value == "normal"
    assert WindowFocusState.FOCUSED.value == "focused"


def test_window_bounds_defaults_and_immutability() -> None:
    bounds = WindowBounds(x=10, y=20, width=800, height=600)
    assert bounds.x == 10
    assert bounds.width == 800

    with pytest.raises((TypeError, ValidationError)):
        bounds.x = 100  # type: ignore


def test_window_info_defaults_and_immutability() -> None:
    info = WindowInfo(window_id="1234", title="Notepad")
    assert info.window_id == "1234"
    assert info.title == "Notepad"

    with pytest.raises((TypeError, ValidationError)):
        info.title = "Other"  # type: ignore


def test_window_operation_result_defaults_and_immutability() -> None:
    res = WindowOperationResult(success=True, window_id="win_1", operation=WindowOperation.FOCUS)
    assert res.success is True
    assert res.window_id == "win_1"

    with pytest.raises((TypeError, ValidationError)):
        res.success = False  # type: ignore
