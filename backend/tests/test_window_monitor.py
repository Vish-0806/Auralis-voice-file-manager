"""Unit tests for WindowMonitor (Phase 11.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.window import (
    WindowInfo,
    WindowMonitor,
    WindowStatistics,
)


def test_window_monitor_start_and_stop() -> None:
    monitor = WindowMonitor()
    active_win = monitor._detector.enumerate_windows()[0]

    monitored = monitor.start_monitoring(active_win.window_id)
    assert isinstance(monitored, WindowInfo)
    assert monitored.window_id == active_win.window_id

    list_mon = monitor.get_monitored_windows()
    assert len(list_mon) == 1

    stopped = monitor.stop_monitoring(active_win.window_id)
    assert stopped is True


def test_window_monitor_statistics() -> None:
    monitor = WindowMonitor()
    monitor.record_operation(success=True)
    monitor.record_operation(success=False)

    stats = monitor.get_statistics()
    assert isinstance(stats, WindowStatistics)
    assert stats.total_operations == 2
    assert stats.successful_operations == 1
    assert stats.failed_operations == 1
