"""Comprehensive unit tests for the Phase 12.1 Brain Execution Engine Subsystem."""

import concurrent.futures
from datetime import datetime
from typing import Any, Dict
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution.execution_models import ExecutionContext
from brain.execution import (
    DecisionEngine,
    DecisionType,
    ExecutionCancelled,
    ExecutionDecision,
    ExecutionException,
    ExecutionFailure,
    ExecutionHealth,
    ExecutionMode,
    ExecutionPipeline,
    ExecutionProvider,
    ExecutionRequest,
    ExecutionResult,
    ExecutionRoutingError,
    ExecutionRuntime,
    ExecutionRuntimeStatus,
    ExecutionState,
    ExecutionStatistics,
    ExecutionStatus,
    ExecutionStepResult,
    ExecutionValidationError,
    IDecisionEngine,
    IExecutionCoordinator,
    IExecutionPipeline,
    IExecutionRuntime,
    IRequestAnalyzer,
    RequestAnalyzer,
    get_execution_runtime,
    reset_execution_runtime,
)


# ============================================================================
# 1. Models & Immutability Tests
# ============================================================================

def test_execution_request_defaults_and_immutability() -> None:
    req = ExecutionRequest(prompt="Open file manager")
    assert req.request_id.startswith("req-")
    assert req.prompt == "Open file manager"
    assert req.mode == ExecutionMode.DEFAULT
    assert isinstance(req.created_at, datetime)

    with pytest.raises((TypeError, ValidationError)):
        req.prompt = "Modified prompt"  # type: ignore


def test_execution_decision_immutability() -> None:
    dec = ExecutionDecision(
        decision_type=DecisionType.DIRECT_EXECUTION,
        requires_planner=False,
        confidence=0.95,
        reason="Simple system command",
    )
    assert dec.decision_type == DecisionType.DIRECT_EXECUTION
    assert dec.confidence == 0.95

    with pytest.raises((TypeError, ValidationError)):
        dec.requires_planner = True  # type: ignore


def test_execution_context_defaults_and_immutability() -> None:
    req = ExecutionRequest(prompt="Test request")
    ctx = ExecutionContext(request=req)
    assert ctx.execution_id.startswith("exec-")
    assert ctx.state == ExecutionState.PENDING
    assert ctx.progress == 0.0

    with pytest.raises((TypeError, ValidationError)):
        ctx.state = ExecutionState.COMPLETED  # type: ignore


def test_execution_result_defaults_and_immutability() -> None:
    res = ExecutionResult(execution_id="exec-123", status=ExecutionStatus.COMPLETED)
    assert res.execution_id == "exec-123"
    assert res.status == ExecutionStatus.COMPLETED
    assert res.state == ExecutionState.COMPLETED

    with pytest.raises((TypeError, ValidationError)):
        res.status = ExecutionStatus.FAILED  # type: ignore


def test_execution_statistics_and_health_models() -> None:
    stats = ExecutionStatistics(total_requests=10, successful_executions=9, failed_executions=1)
    assert stats.total_requests == 10
    assert stats.successful_executions == 9

    health = ExecutionHealth(status="READY", healthy=True, components={"RequestAnalyzer": True})
    assert health.healthy is True
    assert health.components["RequestAnalyzer"] is True


# ============================================================================
# 2. Exceptions Tests
# ============================================================================

def test_execution_exceptions_hierarchy() -> None:
    err = ExecutionValidationError("Invalid input")
    assert isinstance(err, ExecutionException)

    routing_err = ExecutionRoutingError("Routing failed")
    assert isinstance(routing_err, ExecutionException)

    fail_err = ExecutionFailure("Pipeline crash")
    assert isinstance(fail_err, ExecutionException)

    cancel_err = ExecutionCancelled("User aborted")
    assert isinstance(cancel_err, ExecutionException)


# ============================================================================
# 3. Request Analyzer Tests
# ============================================================================

def test_request_analyzer_validation() -> None:
    analyzer = RequestAnalyzer()

    # Valid string
    req1 = analyzer.validate_request("   List desktop files   ")
    assert req1.prompt == "List desktop files"

    # Valid dict
    req2 = analyzer.validate_request({"prompt": "Delete tmp", "user_id": "usr-1"})
    assert req2.prompt == "Delete tmp"
    assert req2.user_id == "usr-1"

    # Invalid None
    with pytest.raises(ExecutionValidationError):
        analyzer.validate_request(None)

    # Invalid empty string
    with pytest.raises(ExecutionValidationError):
        analyzer.validate_request("   ")


def test_request_analyzer_categorization_and_metadata() -> None:
    analyzer = RequestAnalyzer()

    # System command
    req_sys = analyzer.analyze("exec kill process 123")
    assert req_sys.category == "SYSTEM_COMMAND"

    # File operation with path
    req_file = analyzer.analyze("Copy C:/Users/Docs/file.txt to D:/Backup/")
    assert req_file.category == "FILE_OPERATION"
    assert "C:/Users/Docs/file.txt" in req_file.metadata.get("extracted_paths", [])

    # Destructive operation flag
    req_del = analyzer.analyze("force delete all workspace items")
    assert req_del.metadata.get("is_potentially_destructive") is True
    assert req_del.metadata.get("complexity") in ("HIGH", "CRITICAL")


# ============================================================================
# 4. Decision Engine Tests
# ============================================================================

def test_decision_engine_routing_decisions() -> None:
    engine = DecisionEngine()
    analyzer = RequestAnalyzer()

    # Direct execution
    req_direct = analyzer.analyze("Show current status")
    dec_direct = engine.evaluate(req_direct)
    assert dec_direct.decision_type == DecisionType.DIRECT_EXECUTION
    assert dec_direct.requires_planner is False

    # Security review required
    req_sec = analyzer.analyze("format drive C:")
    dec_sec = engine.evaluate(req_sec)
    assert dec_sec.decision_type == DecisionType.SECURITY_REVIEW_REQUIRED
    assert dec_sec.requires_security_review is True

    # Planner required
    req_plan = analyzer.analyze("organize directory and then clean files and then compress log folder")
    dec_plan = engine.evaluate(req_plan)
    assert dec_plan.decision_type == DecisionType.PLANNER_REQUIRED
    assert dec_plan.requires_planner is True

    # AI required
    req_ai = analyzer.analyze("write an essay summarizing user preferences")
    dec_ai = engine.evaluate(req_ai)
    assert dec_ai.decision_type == DecisionType.AI_REQUIRED
    assert dec_ai.requires_ai is True


# ============================================================================
# 5. Execution Pipeline Tests
# ============================================================================

class MockSubsystemRuntime:
    def __init__(self, response_name: str) -> None:
        self.response_name = response_name
        self.called = False

    def generate(self, prompt: str) -> str:
        self.called = True
        return f"{self.response_name}_response"

    def process_reasoning_context(self, ctx: Any) -> Any:
        self.called = True
        return "mock_plan"

    def evaluate_request(self, req: Any) -> Any:
        self.called = True
        return "APPROVED"

    def execute(self, action: str) -> str:
        self.called = True
        return f"{self.response_name}_executed"


def test_execution_pipeline_orchestration() -> None:
    mock_ai = MockSubsystemRuntime("AI")
    mock_plan = MockSubsystemRuntime("Planner")
    mock_sec = MockSubsystemRuntime("Security")
    mock_os = MockSubsystemRuntime("OS")

    pipeline = ExecutionPipeline(
        ai_runtime=mock_ai,
        planning_runtime=mock_plan,
        security_runtime=mock_sec,
        os_runtime=mock_os,
    )

    req = ExecutionRequest(prompt="generate script and plan actions")
    dec = ExecutionDecision(
        decision_type=DecisionType.AI_REQUIRED,
        requires_ai=True,
        requires_planner=True,
        requires_security_review=True,
    )

    result = pipeline.execute(req, dec)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.completed_steps == 5
    assert mock_ai.called is True
    assert mock_plan.called is True
    assert mock_sec.called is True
    assert mock_os.called is True


# ============================================================================
# 6. Execution Provider & Statistics Tests
# ============================================================================

def test_execution_provider_end_to_end_and_statistics() -> None:
    provider = ExecutionProvider()
    provider.clear()

    res1 = provider.execute("Open system settings")
    assert res1.status == ExecutionStatus.COMPLETED

    res2 = provider.execute("summarize document")
    assert res2.status == ExecutionStatus.COMPLETED

    stats = provider.get_statistics()
    assert stats.total_requests == 2
    assert stats.successful_executions == 2
    assert stats.failed_executions == 0

    health = provider.health_check()
    assert health.healthy is True
    assert health.status == "READY"


# ============================================================================
# 7. Execution Runtime Lifecycle & Singleton Tests
# ============================================================================

def test_execution_runtime_lifecycle() -> None:
    reset_execution_runtime()

    rt = get_execution_runtime()
    assert rt.status == ExecutionRuntimeStatus.READY

    result = rt.process_request("Create new directory")
    assert result.status == ExecutionStatus.COMPLETED

    health = rt.health_check()
    assert health.healthy is True

    stats = rt.get_statistics()
    assert stats.total_requests == 1

    assert rt.shutdown() is True
    assert rt.status == ExecutionRuntimeStatus.SHUTDOWN

    reset_execution_runtime()


def test_execution_runtime_singleton_identity() -> None:
    reset_execution_runtime()
    rt1 = get_execution_runtime()
    rt2 = get_execution_runtime()
    assert rt1 is rt2

    reset_execution_runtime()
    rt3 = get_execution_runtime()
    assert rt3 is not rt1
    reset_execution_runtime()


# ============================================================================
# 8. Thread Safety & Concurrency Tests
# ============================================================================

def test_execution_runtime_thread_safety() -> None:
    reset_execution_runtime()
    rt = get_execution_runtime()

    def worker(idx: int) -> ExecutionResult:
        return rt.process_request(f"Concurrent request {idx}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 20
    assert all(r.status == ExecutionStatus.COMPLETED for r in results)

    stats = rt.get_statistics()
    assert stats.total_requests == 20
    assert stats.successful_executions == 20

    reset_execution_runtime()
