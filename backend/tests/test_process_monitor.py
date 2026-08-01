"""Unit tests for ProcessMonitor (Phase 11.4)."""

import os
# pyrefly: ignore [missing-import]
import pytest

from brain.os.process import (
    ProcessMonitor,
    ProcessStatistics,
    RunningProcess,
)


def test_process_monitor_start_and_stop() -> None:
    monitor = ProcessMonitor()
    curr_pid = os.getpid()

    running = monitor.start_monitoring(curr_pid)
    assert isinstance(running, RunningProcess)
    assert running.info.process_id == curr_pid

    monitored = monitor.get_monitored_processes()
    assert len(monitored) >= 1
    pids = [m.info.process_id for m in monitored]
    assert curr_pid in pids

    stopped = monitor.stop_monitoring(curr_pid)
    assert stopped is True


def test_process_monitor_statistics() -> None:
    monitor = ProcessMonitor()
    monitor.record_termination(success=True)
    monitor.record_termination(success=False)

    stats = monitor.get_statistics()
    assert isinstance(stats, ProcessStatistics)
    assert stats.total_terminations == 2
    assert stats.successful_terminations == 1
    assert stats.failed_terminations == 1
