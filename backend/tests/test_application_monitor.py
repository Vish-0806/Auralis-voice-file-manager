"""Unit tests for ApplicationMonitor (Phase 11.3)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.application import (
    ApplicationMonitor,
    ApplicationStatistics,
    RunningApplication,
)


def test_application_monitor_register_and_unregister() -> None:
    monitor = ApplicationMonitor()

    running = monitor.register_process(
        process_id=9876,
        app_id="app_test",
        executable_path="/bin/test",
        name="TestApp",
    )

    assert isinstance(running, RunningApplication)
    assert running.process_id == 9876
    assert running.name == "TestApp"

    active_apps = monitor.get_running_applications()
    assert len(active_apps) == 1
    assert active_apps[0].process_id == 9876

    single = monitor.get_running_application(9876)
    assert single is not None
    assert single.app_id == "app_test"

    unregistered = monitor.unregister_process(9876)
    assert unregistered is True
    assert len(monitor.get_running_applications()) == 0


def test_application_monitor_statistics() -> None:
    monitor = ApplicationMonitor()

    monitor.record_launch(success=True, duration_ms=50.0)
    monitor.record_launch(success=True, duration_ms=150.0)
    monitor.record_launch(success=False, duration_ms=0.0)

    stats = monitor.get_statistics()
    assert isinstance(stats, ApplicationStatistics)
    assert stats.total_launches == 3
    assert stats.successful_launches == 2
    assert stats.failed_launches == 1
    assert stats.average_launch_time_ms == 100.0
