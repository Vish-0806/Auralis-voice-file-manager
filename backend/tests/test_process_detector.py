"""Unit tests for ProcessDetector (Phase 11.4)."""

import os
# pyrefly: ignore [missing-import]
import pytest

from brain.os.process import ProcessDetector, ProcessInfo


def test_process_detector_enumerate_and_lookup() -> None:
    detector = ProcessDetector()
    procs = detector.enumerate_processes()
    assert isinstance(procs, list)
    assert len(procs) > 0

    curr_pid = os.getpid()
    curr_info = detector.get_by_pid(curr_pid)
    assert curr_info is not None
    assert curr_info.process_id == curr_pid
    assert len(curr_info.name) > 0


def test_process_detector_get_by_name() -> None:
    detector = ProcessDetector()
    curr_info = detector.get_by_pid(os.getpid())
    assert curr_info is not None

    by_name = detector.get_by_name(curr_info.name)
    assert len(by_name) > 0
    pids = [p.process_id for p in by_name]
    assert curr_info.process_id in pids
