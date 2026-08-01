"""Unit tests for WindowController (Phase 11.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.window import (
    WindowBounds,
    WindowController,
    WindowOperationResult,
)


def test_window_controller_operations() -> None:
    ctrl = WindowController()

    # Retrieve an active window identifier
    wins = ctrl._service._detector.enumerate_windows()
    target_id = wins[0].window_id

    res_focus = ctrl.focus(target_id)
    assert isinstance(res_focus, WindowOperationResult)
    assert res_focus.success is True

    res_min = ctrl.minimize(target_id)
    assert res_min.success is True

    res_res = ctrl.restore(target_id)
    assert res_res.success is True

    res_move = ctrl.move_and_resize(target_id, WindowBounds(x=150, y=150, width=900, height=700))
    assert res_move.success is True
