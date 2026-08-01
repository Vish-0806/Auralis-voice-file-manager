"""Unit tests for DeviceMonitor (Phase 11.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.device import (
    DeviceInfo,
    DeviceMonitor,
    DeviceStatistics,
)


def test_device_monitor_start_and_stop() -> None:
    monitor = DeviceMonitor()
    target_id = "audio_out_primary"

    monitored = monitor.start_monitoring(target_id)
    assert isinstance(monitored, DeviceInfo)
    assert monitored.device_id == target_id

    list_mon = monitor.get_monitored_devices()
    assert len(list_mon) == 1

    stopped = monitor.stop_monitoring(target_id)
    assert stopped is True


def test_device_monitor_statistics() -> None:
    monitor = DeviceMonitor()
    monitor.record_operation(success=True)
    monitor.record_operation(success=False)

    stats = monitor.get_statistics()
    assert isinstance(stats, DeviceStatistics)
    assert stats.total_operations == 2
    assert stats.successful_operations == 1
    assert stats.failed_operations == 1
