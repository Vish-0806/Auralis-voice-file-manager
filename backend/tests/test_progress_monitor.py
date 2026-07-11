"""Unit tests for the Auralis Progress Monitoring subsystem."""

from __future__ import annotations

import time
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from core.intents import Intent
from core.models import ExecutionResult
from brain.capability.models import RoutedExecutionPlan, CapabilityRoute
from brain.execution.models import ExecutionStatus
from brain.execution.execution_engine import ExecutionEngine
from brain.monitoring.models import ExecutionEvent, ExecutionProgress, ExecutionMetrics, ProgressUpdate
from brain.monitoring.execution_tracker import ExecutionTracker
from brain.monitoring.metrics_collector import MetricsCollector
from brain.monitoring.event_stream import EventStream
from brain.monitoring.progress_monitor import ProgressMonitor


# --- Models Validation Tests ---

def test_progress_models_validation():
    """Validates that progress models compile and validate correctly."""
    progress = ExecutionProgress(
        execution_id="exec_1",
        current_step="step_1",
        completed_steps=["step_0"],
        remaining_steps=["step_2"],
        elapsed_time=1.5,
        estimated_remaining_time=1.5,
        percent_complete=50.0,
    )
    assert progress.execution_id == "exec_1"
    assert progress.percent_complete == 50.0

    metrics = ExecutionMetrics(
        execution_duration=3.0,
        average_step_duration=1.5,
        success_rate=100.0,
        failure_rate=0.0,
        recovery_count=0,
    )
    assert metrics.success_rate == 100.0

    update = ProgressUpdate(
        event_type=ExecutionEvent.StepCompleted,
        progress=progress,
        metrics=metrics,
        timestamp=time.time(),
    )
    assert update.event_type == ExecutionEvent.StepCompleted


# --- Execution Tracker Tests ---

def test_execution_tracker():
    """Validates percentage completion and elapsed estimations."""
    tracker = ExecutionTracker(execution_id="exec_123", total_steps=["step_1", "step_2"])
    
    # Session starts: 0% complete, estimated remaining time defaults to 1s per step
    prog0 = tracker.get_progress()
    assert prog0.percent_complete == 0.0
    assert prog0.estimated_remaining_time == 2.0  # 2 remaining steps * 1.0s

    # Start first step
    tracker.start_step("step_1")
    prog1 = tracker.get_progress()
    assert prog1.current_step == "step_1"
    assert "step_1" not in prog1.remaining_steps

    # Complete first step
    time.sleep(0.01)  # tiny delay
    tracker.complete_step("step_1")
    prog2 = tracker.get_progress()
    assert prog2.current_step is None
    assert "step_1" in prog2.completed_steps
    assert prog2.percent_complete == 50.0
    assert prog2.estimated_remaining_time > 0.0


# --- Metrics Collector Tests ---

def test_metrics_collector():
    """Validates aggregation of success/failure rates and averages."""
    collector = MetricsCollector()
    collector.record_step_result(0.5, success=True)
    collector.record_step_result(1.5, success=False)
    collector.record_recovery()
    collector.set_execution_duration(2.0)

    metrics = collector.get_metrics()
    assert metrics.average_step_duration == 1.0
    assert metrics.success_rate == 50.0
    assert metrics.failure_rate == 50.0
    assert metrics.recovery_count == 1
    assert metrics.execution_duration == 2.0


# --- Event Stream Tests ---

def test_event_stream_publishing():
    """Validates subscription callbacks and wildcard events distribution."""
    stream = EventStream()
    
    specific_calls = []
    wildcard_calls = []

    stream.subscribe("StepCompleted", lambda update: specific_calls.append(update))
    stream.subscribe("*", lambda update: wildcard_calls.append(update))

    progress = ExecutionProgress(execution_id="1", completed_steps=[], remaining_steps=[])
    metrics = ExecutionMetrics()
    update = ProgressUpdate(
        event_type=ExecutionEvent.StepCompleted,
        progress=progress,
        metrics=metrics,
        timestamp=time.time(),
    )

    stream.publish(update)

    assert len(specific_calls) == 1
    assert len(wildcard_calls) == 1
    assert specific_calls[0].event_type == ExecutionEvent.StepCompleted


# --- Progress Monitor Tests ---

def test_progress_monitor_stall_check():
    """Validates stall checks against defined threshold parameters."""
    monitor = ProgressMonitor()
    assert monitor.check_stalled(step_elapsed=6.0, threshold_seconds=5.0) is True
    assert monitor.check_stalled(step_elapsed=2.0, threshold_seconds=5.0) is False


# --- Integration with Execution Engine Tests ---

def test_execution_engine_progress_integration():
    """Validates that running a plan successfully triggers all progress monitoring notifications in sequence."""
    monitor = ProgressMonitor()
    
    events_logged = []
    monitor.event_stream.subscribe("*", lambda update: events_logged.append(update.event_type))

    engine = ExecutionEngine(progress_monitor=monitor)

    mock_dispatcher = MagicMock()
    mock_dispatcher._capabilities = {"desktop": MagicMock()}
    mock_dispatcher.dispatch.return_value = ExecutionResult(
        success=True,
        response="OK",
        execution_time=0.01,
    )

    plan = RoutedExecutionPlan(
        intent=Intent.MUTE,
        confidence=1.0,
        routes=[CapabilityRoute(step_id="step_1", intent=Intent.MUTE, capability_name="Desktop")],
    )

    engine.execute_plan(plan, mock_dispatcher)

    # Check sequential event log triggers
    expected_sequence = [
        ExecutionEvent.ExecutionStarted,
        ExecutionEvent.StepStarted,
        ExecutionEvent.StepCompleted,
        ExecutionEvent.ExecutionCompleted,
    ]
    assert events_logged == expected_sequence
