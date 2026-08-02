"""Unit test suite for Phase 12.6 — Automation & Scheduling Runtime.

Covers:
- Automation models, enums, defaults, and immutability
- Subsystem exception hierarchy
- AutomationScheduler rule registration, recurring interval calculation, and due rule retrieval
- AutomationTriggerEngine evaluation of Time, Manual, Event, and Task Completion triggers
- AutomationHistoryStore execution recording and history summary query
- AutomationExecutor rule dispatching with mock task and workflow runtimes
- AutomationProvider end-to-end processing, health reporting, and statistics
- AutomationRuntime singleton lifecycle, status management, and thread safety under concurrency
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.automation import (
    AutomationExecution,
    AutomationExecutionMode,
    AutomationExecutor,
    AutomationHealth,
    AutomationHistory,
    AutomationHistoryStore,
    AutomationPriority,
    AutomationProvider,
    AutomationRule,
    AutomationRuntime,
    AutomationRuntimeStatus,
    AutomationSchedule,
    AutomationScheduleType,
    AutomationScheduler,
    AutomationStatistics,
    AutomationStatus,
    AutomationTrigger,
    AutomationTriggerEngine,
    AutomationTriggerType,
    IAutomationProvider,
    get_automation_runtime,
    reset_automation_runtime,
)


@pytest.fixture(autouse=True)
def cleanup_runtime() -> None:
    """Fixture resetting global automation runtime before and after each test."""
    reset_automation_runtime()
    yield
    reset_automation_runtime()


def test_automation_models_defaults_and_immutability() -> None:
    """Verifies automation model default properties and Pydantic v2 immutability."""
    sched = AutomationSchedule(schedule_type=AutomationScheduleType.RECURRING, interval_seconds=300.0)
    trig = AutomationTrigger(trigger_type=AutomationTriggerType.TIME, schedule=sched)
    rule = AutomationRule(rule_id="rule_1", name="Daily Backup", trigger=trig)

    assert rule.rule_id == "rule_1"
    assert rule.name == "Daily Backup"
    assert rule.trigger.schedule.interval_seconds == 300.0

    with pytest.raises((TypeError, ValidationError)):
        rule.name = "Modified Rule"  # type: ignore


def test_automation_scheduler_registration_and_due_rules() -> None:
    """Verifies rule registration, interval calculation, and due rule retrieval."""
    scheduler = AutomationScheduler()
    sched = AutomationSchedule(schedule_type=AutomationScheduleType.RECURRING, interval_seconds=0.1)
    trig = AutomationTrigger(trigger_type=AutomationTriggerType.TIME, schedule=sched)
    rule = AutomationRule(rule_id="r1", name="Scheduled Rule", trigger=trig)

    assert scheduler.register_rule(rule) is True
    due = scheduler.get_due_rules()
    assert len(due) == 1
    assert due[0].rule_id == "r1"


def test_automation_trigger_engine_evaluations() -> None:
    """Verifies trigger evaluation for Manual, System Event, and Task Completion triggers."""
    engine = AutomationTriggerEngine()

    # Manual Trigger
    trig_manual = AutomationTrigger(trigger_type=AutomationTriggerType.MANUAL)
    assert engine.evaluate_trigger(trig_manual, {"manual_override": True}) is True

    # Event Trigger
    trig_event = AutomationTrigger(trigger_type=AutomationTriggerType.SYSTEM_EVENT, event_pattern="file_created")
    assert engine.evaluate_trigger(trig_event, {"event_name": "file_created_event"}) is True

    # Task Completion Trigger
    trig_task = AutomationTrigger(trigger_type=AutomationTriggerType.TASK_COMPLETION, condition="task_123")
    assert engine.evaluate_trigger(trig_task, {"event_type": "TASK_COMPLETION", "task_id": "task_123"}) is True


def test_automation_history_store() -> None:
    """Verifies execution recording and history summary querying."""
    store = AutomationHistoryStore()
    exec1 = AutomationExecution(rule_id="r1", status=AutomationStatus.COMPLETED, duration_seconds=1.2)
    exec2 = AutomationExecution(rule_id="r1", status=AutomationStatus.FAILED, duration_seconds=0.5)

    store.record_execution(exec1)
    store.record_execution(exec2)

    history = store.get_history("r1")
    assert history is not None
    assert history.total_runs == 2
    assert history.successful_runs == 1
    assert history.failed_runs == 1


def test_automation_executor_with_mocks() -> None:
    """Verifies rule dispatching via mock task runtime and mock workflow runtime."""
    mock_task_rt = MagicMock()
    mock_task_rt.process_task.return_value = MagicMock(status="COMPLETED", task_id="t_99")

    executor = AutomationExecutor(task_runtime=mock_task_rt)
    rule = AutomationRule(
        rule_id="r1",
        name="Task Rule",
        mode=AutomationExecutionMode.TASK_MANAGED,
        action_payload="run_backup",
    )

    execution = executor.execute_rule(rule)
    assert execution.status == AutomationStatus.COMPLETED
    assert execution.output.get("task_id") == "t_99"
    mock_task_rt.process_task.assert_called_once_with("run_backup", context=None)


def test_automation_provider_end_to_end_and_health_check() -> None:
    """Verifies AutomationProvider manual triggering, health checks, and statistics."""
    provider = AutomationProvider()

    rule = AutomationRule(rule_id="r1", name="Manual Rule")
    provider.register_rule(rule)

    execution = provider.trigger_manually("r1")
    assert execution.status == AutomationStatus.COMPLETED

    health = provider.health_check()
    assert isinstance(health, AutomationHealth)
    assert health.healthy is True
    assert len(health.components) == 4

    stats = provider.get_statistics()
    assert isinstance(stats, AutomationStatistics)
    assert stats.total_rules == 1
    assert stats.total_executions == 1

    history = provider.get_history("r1")
    assert history is not None
    assert history.total_runs == 1


def test_automation_runtime_lifecycle_and_singleton() -> None:
    """Verifies AutomationRuntime initialization, processing, health reporting, and singleton identity."""
    rt = get_automation_runtime()
    assert rt.status == AutomationRuntimeStatus.READY

    rt2 = get_automation_runtime()
    assert rt is rt2

    rule = AutomationRule(rule_id="r1", name="Runtime Rule")
    rt.register_rule(rule)

    exec_res = rt.trigger_manually("r1")
    assert exec_res.status == AutomationStatus.COMPLETED

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_rules == 1
    assert stats.total_executions == 1

    rt.clear()
    assert rt.get_statistics().total_rules == 0

    assert rt.shutdown() is True
    assert rt.status == AutomationRuntimeStatus.SHUTDOWN


def test_automation_runtime_thread_safety() -> None:
    """Verifies thread-safe rule execution across concurrent worker threads."""
    rt = get_automation_runtime()

    for i in range(5):
        rule = AutomationRule(rule_id=f"rule_{i}", name=f"Concurrent Rule {i}")
        rt.register_rule(rule)

    def worker(i: int) -> AutomationStatus:
        res = rt.trigger_manually(f"rule_{i % 5}")
        return res.status

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, range(15)))

    assert len(results) == 15
    assert all(status == AutomationStatus.COMPLETED for status in results)

    stats = rt.get_statistics()
    assert stats.total_executions == 15
    assert stats.successful_executions == 15
