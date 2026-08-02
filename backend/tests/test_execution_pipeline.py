"""End-to-End Execution Pipeline Integration Test Suite (Phase 12.10).

Validates the full execution architecture across all 9 execution runtimes:
- Phase 12.1: Brain Execution Engine
- Phase 12.2: Intent Resolution Engine
- Phase 12.3: Command Execution Orchestrator
- Phase 12.4: Workflow Execution Engine
- Phase 12.5: Task Management Runtime
- Phase 12.6: Automation & Scheduling Runtime
- Phase 12.7: Execution Analytics & Observability Runtime
- Phase 12.8: Execution Recovery & State Management Runtime
- Phase 12.9: Execution Runtime Integration
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest

from brain.execution.analytics import (
    AuditSeverity,
    ExecutionOutcome,
    MetricType,
    TraceLevel,
    get_analytics_runtime,
    reset_analytics_runtime,
)
from brain.execution.automation import (
    AutomationPriority,
    AutomationRule,
    AutomationSchedule,
    AutomationScheduleType,
    AutomationStatus,
    AutomationTrigger,
    AutomationTriggerType,
    get_automation_runtime,
    reset_automation_runtime,
)
from brain.execution.intent import (
    IntentCategory,
    ResolutionStatus,
    get_intent_runtime,
    reset_intent_runtime,
)
from brain.execution.integration import (
    ExecutionCapability,
    ExecutionPriority,
    ExecutionStage,
    ExecutionStatus,
    ExecutionTarget,
    IntegrationHealth,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
    get_execution_runtime,
    reset_execution_runtime,
)
from brain.execution.orchestrator import (
    get_orchestrator_runtime,
    reset_orchestrator_runtime,
)
from brain.execution.recovery import (
    CheckpointType,
    RecoveryStatus,
    RecoveryStrategy,
    RollbackStatus,
    get_recovery_runtime,
    reset_recovery_runtime,
)
from brain.execution.task import (
    TaskPriority,
    TaskRequest,
    TaskStatus,
    get_task_runtime,
    reset_task_runtime,
)
from brain.execution.workflow import (
    WorkflowDependency,
    WorkflowRequest,
    WorkflowStatus,
    WorkflowStep,
    get_workflow_runtime,
    reset_workflow_runtime,
)


@pytest.fixture(autouse=True)
def reset_all_execution_runtimes() -> None:
    """Fixture resetting all 9 execution runtimes before and after each test."""
    reset_execution_runtime()
    reset_recovery_runtime()
    reset_analytics_runtime()
    reset_automation_runtime()
    reset_task_runtime()
    reset_workflow_runtime()
    reset_orchestrator_runtime()
    reset_intent_runtime()
    yield
    reset_execution_runtime()
    reset_recovery_runtime()
    reset_analytics_runtime()
    reset_automation_runtime()
    reset_task_runtime()
    reset_workflow_runtime()
    reset_orchestrator_runtime()
    reset_intent_runtime()


def test_e2e_runtime_initialization_all_subsystems() -> None:
    """Verifies simultaneous initialization and health status of all 9 execution runtimes."""
    rt_integration = get_execution_runtime()
    rt_recovery = get_recovery_runtime()
    rt_analytics = get_analytics_runtime()
    rt_automation = get_automation_runtime()
    rt_task = get_task_runtime()
    rt_workflow = get_workflow_runtime()
    rt_orchestrator = get_orchestrator_runtime()
    rt_intent = get_intent_runtime()

    assert rt_integration.status.value in ("READY", "INITIALIZING")
    assert rt_recovery.status.value in ("READY", "INITIALIZING")
    assert rt_analytics.status.value in ("READY", "INITIALIZING")
    assert rt_automation.status.value in ("READY", "INITIALIZING")
    assert rt_task.status.value in ("READY", "INITIALIZING")
    assert rt_workflow.status.value in ("READY", "INITIALIZING")
    assert rt_orchestrator.status.value in ("READY", "INITIALIZING")
    assert rt_intent.status.value in ("READY", "INITIALIZING")


def test_e2e_request_pipeline_complete_flow() -> None:
    """Verifies end-to-end request processing flow through Intent → Command → Recovery → Analytics → Response."""
    integration_rt = get_execution_runtime()

    req = IntegrationRequest(
        user_input="Execute file cleanup command",
        priority=ExecutionPriority.HIGH,
        correlation_id="corr-e2e-001",
    )

    resp = integration_rt.process_request(req)

    assert resp.status == ExecutionStatus.COMPLETED
    assert resp.request_id == req.request_id
    assert resp.target == ExecutionTarget.COMMAND_ORCHESTRATOR
    assert resp.result_data.get("intent_resolved") is True
    assert resp.result_data.get("security_cleared") is True
    assert resp.result_data.get("checkpoint_saved") is True
    assert resp.result_data.get("analytics_recorded") is True


def test_e2e_intent_resolution_delegation() -> None:
    """Verifies intent recognition and entity extraction delegation."""
    intent_rt = get_intent_runtime()

    res = intent_rt.process_intent("Search for quarterly report.pdf")
    assert res.status == ResolutionStatus.RESOLVED
    assert res.primary_intent.category == IntentCategory.FILE_SEARCH


def test_e2e_workflow_engine_multi_step_delegation() -> None:
    """Verifies workflow graph creation, topological scheduling, and multi-step execution."""
    wf_rt = get_workflow_runtime()

    step1 = WorkflowStep(step_id="step_read", name="Read Input Files", action="read_files")
    step2 = WorkflowStep(step_id="step_process", name="Process Files", action="process_data")

    wf_exec = wf_rt.process_workflow([step1, step2])
    assert wf_exec.status == WorkflowStatus.COMPLETED
    assert wf_exec.completed_steps == 2


def test_e2e_task_runtime_scheduling_and_monitoring() -> None:
    """Verifies task submission, priority queuing, and progress monitoring."""
    task_rt = get_task_runtime()

    t_req = TaskRequest(
        task_id="t_e2e_1",
        name="Long Running Archive Task",
        payload={"target_dir": "/data/archive"},
        priority=TaskPriority.HIGH,
    )

    task_exec = task_rt.process_task(t_req)
    assert task_exec.status == TaskStatus.COMPLETED
    assert task_exec.task_id == "t_e2e_1"


def test_e2e_automation_rule_trigger_evaluation() -> None:
    """Verifies automation rule registration, trigger evaluation, and execution history."""
    auto_rt = get_automation_runtime()

    rule = AutomationRule(
        rule_id="r_e2e_1",
        name="Nightly Maintenance Rule",
        trigger=AutomationTrigger(trigger_type=AutomationTriggerType.TIME, expression="0 0 * * *"),
        schedule=AutomationSchedule(schedule_type=AutomationScheduleType.CRON, cron_expression="0 0 * * *"),
        action="run_maintenance",
    )

    auto_rt.register_rule(rule)
    exec_result = auto_rt.trigger_manually("r_e2e_1")
    assert exec_result.status == AutomationStatus.COMPLETED


def test_e2e_recovery_checkpoint_and_state_restoration() -> None:
    """Verifies checkpoint creation during execution and state restoration strategy."""
    rec_rt = get_recovery_runtime()

    chk = rec_rt.create_checkpoint(
        execution_id="exec_e2e_100",
        state_data={"step_index": 3, "buffer": [1, 2, 3]},
        checkpoint_type=CheckpointType.STAGE,
    )
    assert chk.execution_id == "exec_e2e_100"

    rec_exec = rec_rt.recover_execution("exec_e2e_100", strategy=RecoveryStrategy.RESUME_CHECKPOINT)
    assert rec_exec.status == RecoveryStatus.SUCCESS
    assert rec_exec.restored_state.get("step_index") == 3

    rb_exec = rec_rt.rollback_execution("exec_e2e_100", target_checkpoint_id=chk.checkpoint_id)
    assert rb_exec.status == RollbackStatus.COMPLETED


def test_e2e_analytics_metrics_tracing_and_audit() -> None:
    """Verifies metric collection, trace span correlation, and audit logging across execution pipeline."""
    analytics_rt = get_analytics_runtime()

    analytics_rt.record_metric("pipeline_latency", 42.5, metric_type=MetricType.TIMER, unit="ms")
    span_id = analytics_rt.start_trace("Pipeline Step Execution", correlation_id="corr-analytics-100")
    analytics_rt.log_audit("PIPELINE", "IntegrationProvider", "Completed Stage", severity=AuditSeverity.LOW)
    trace = analytics_rt.stop_trace(span_id)

    assert trace.correlation_id == "corr-analytics-100"
    stats = analytics_rt.get_statistics()
    assert stats.total_metrics_collected == 1
    assert stats.total_traces_recorded == 1
    assert stats.total_audit_records == 1


def test_e2e_health_check_reporting_all_subsystems() -> None:
    """Verifies health check reporting across all execution subsystems."""
    integration_rt = get_execution_runtime()

    health = integration_rt.health_check()
    assert isinstance(health, IntegrationHealth)
    assert health.healthy is True
    assert len(health.subsystems) >= 10


def test_e2e_statistics_and_diagnostics() -> None:
    """Verifies aggregate statistics collection across pipeline executions."""
    integration_rt = get_execution_runtime()

    for i in range(3):
        req = IntegrationRequest(user_input=f"Batch execution request {i}")
        integration_rt.process_request(req)

    stats = integration_rt.get_statistics()
    assert isinstance(stats, IntegrationStatistics)
    assert stats.total_requests == 3
    assert stats.successful_executions == 3
    assert stats.average_latency_ms >= 0.0


def test_e2e_graceful_error_handling() -> None:
    """Verifies system stability and graceful error handling on malformed requests."""
    integration_rt = get_execution_runtime()

    req = IntegrationRequest(user_input="", metadata={"target": "NON_EXISTENT_TARGET"})
    resp = integration_rt.process_request(req)

    assert resp is not None
    assert resp.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED)


def test_e2e_multithreaded_high_concurrency_stress() -> None:
    """Verifies multithreaded thread safety under high concurrency across all runtimes."""
    integration_rt = get_execution_runtime()
    recovery_rt = get_recovery_runtime()
    analytics_rt = get_analytics_runtime()

    def worker(i: int) -> str:
        req = IntegrationRequest(
            user_input=f"Concurrent request {i}",
            correlation_id=f"corr-worker-{i}",
        )
        resp = integration_rt.process_request(req)
        recovery_rt.create_checkpoint(f"exec_worker_{i}", {"worker_id": i})
        analytics_rt.record_metric("worker_metric", float(i))
        return resp.execution_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(worker, range(20)))

    assert len(results) == 20

    stats = integration_rt.get_statistics()
    assert stats.total_requests == 20
    assert stats.successful_executions == 20
