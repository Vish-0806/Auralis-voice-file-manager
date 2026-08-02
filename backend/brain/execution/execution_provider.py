"""Execution Provider for the Auralis Brain Execution Engine Subsystem (Phase 12.1).

Aggregates RequestAnalyzer, DecisionEngine, and ExecutionPipeline into a unified execution gateway.
Exposes health, statistics, and diagnostic entry points. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.decision_engine import DecisionEngine
from brain.execution.execution_models import (
    ExecutionDecision,
    ExecutionHealth,
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
    ExecutionStatistics,
    ExecutionStatus,
)
from brain.execution.execution_pipeline import ExecutionPipeline
from brain.execution.interfaces import (
    IExecutionCoordinator,
    IDecisionEngine,
    IExecutionPipeline,
    IRequestAnalyzer,
)
from brain.execution.request_analyzer import RequestAnalyzer

logger = logging.getLogger(__name__)


class ExecutionProvider(IExecutionCoordinator):
    """Thread-safe aggregate coordinator uniting Analyzer, Decision Engine, and Pipeline."""

    def __init__(
        self,
        analyzer: Optional[IRequestAnalyzer] = None,
        decision_engine: Optional[IDecisionEngine] = None,
        pipeline: Optional[IExecutionPipeline] = None,
    ) -> None:
        """Initializes the ExecutionProvider with optional component instances."""
        self._lock = threading.RLock()
        self._analyzer = analyzer or RequestAnalyzer()
        self._decision_engine = decision_engine or DecisionEngine()
        self._pipeline = pipeline or ExecutionPipeline()

        # Statistics state
        self._total_requests = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._cancelled_executions = 0
        self._total_execution_time_ms = 0.0
        self._decisions_by_type: Dict[str, int] = {}
        self._active_sessions = 0

    @property
    def analyzer(self) -> IRequestAnalyzer:
        return self._analyzer

    @property
    def decision_engine(self) -> IDecisionEngine:
        return self._decision_engine

    @property
    def pipeline(self) -> IExecutionPipeline:
        return self._pipeline

    def execute_request(self, request: Any) -> ExecutionResult:
        """Execute request end-to-end: Analyze -> Decide -> Orchestrate -> Report."""
        return self.execute(request)

    def execute(self, request: Any) -> ExecutionResult:
        """Main execution entry point uniting analysis, routing, and pipeline execution.

        Args:
            request: ExecutionRequest, dict, BrainRequest, or raw prompt string.

        Returns:
            Immutable ExecutionResult object.
        """
        with self._lock:
            self._total_requests += 1
            self._active_sessions += 1

        try:
            # 1. Analyze & Normalize Request
            analyzed_req: ExecutionRequest = self._analyzer.analyze(request)

            # 2. Formulate Decision
            decision: ExecutionDecision = self._decision_engine.evaluate(analyzed_req)
            dec_type_str = decision.decision_type.value if hasattr(decision.decision_type, "value") else str(decision.decision_type)

            with self._lock:
                self._decisions_by_type[dec_type_str] = self._decisions_by_type.get(dec_type_str, 0) + 1

            # Check if decision requires immediate interactive clarification or security rejection
            if decision.requires_clarification and not analyzed_req.prompt.strip():
                result = ExecutionResult(
                    execution_id=f"exec-clarify-{analyzed_req.request_id}",
                    status=ExecutionStatus.WAITING_FOR_CONFIRMATION,
                    state=ExecutionState.PAUSED,
                    output={"message": decision.reason, "action": decision.recommended_action},
                )
                with self._lock:
                    self._successful_executions += 1
                return result

            # 3. Execute Pipeline Orchestration
            result: ExecutionResult = self._pipeline.execute(analyzed_req, decision)

            # 4. Record Metrics
            with self._lock:
                if result.status == ExecutionStatus.COMPLETED or result.state == ExecutionState.COMPLETED:
                    self._successful_executions += 1
                elif result.status == ExecutionStatus.CANCELLED or result.state == ExecutionState.CANCELLED:
                    self._cancelled_executions += 1
                else:
                    self._failed_executions += 1

                self._total_execution_time_ms += result.execution_time

            return result

        except Exception as exc:
            logger.error("ExecutionProvider.execute failed: %s", exc)
            with self._lock:
                self._failed_executions += 1

            return ExecutionResult(
                execution_id=f"exec-error-{hash(str(request)) & 0xFFFFFFFF:08x}",
                status=ExecutionStatus.FAILED,
                state=ExecutionState.FAILED,
                error=str(exc),
                finished_at=datetime.now(timezone.utc),
            )
        finally:
            with self._lock:
                self._active_sessions = max(0, self._active_sessions - 1)

    def health_check(self) -> ExecutionHealth:
        """Return real-time diagnostic health report of the Execution Engine provider."""
        with self._lock:
            components = {
                "RequestAnalyzer": self._analyzer is not None,
                "DecisionEngine": self._decision_engine is not None,
                "ExecutionPipeline": self._pipeline is not None,
            }
            is_healthy = all(components.values())
            issues: List[str] = []
            if not is_healthy:
                issues.append("One or more execution provider sub-components are missing")

            return ExecutionHealth(
                status="READY" if is_healthy else "DEGRADED",
                healthy=is_healthy,
                components=components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "RLock_PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Return snapshot of execution metrics and decision statistics."""
        with self._lock:
            avg_ms = (self._total_execution_time_ms / self._total_requests) if self._total_requests > 0 else 0.0
            return ExecutionStatistics(
                total_requests=self._total_requests,
                successful_executions=self._successful_executions,
                failed_executions=self._failed_executions,
                cancelled_executions=self._cancelled_executions,
                average_execution_time_ms=avg_ms,
                decisions_by_type=dict(self._decisions_by_type),
                active_sessions=self._active_sessions,
                metadata={},
            )

    def clear(self) -> None:
        """Reset execution statistics and transient session counts."""
        with self._lock:
            self._total_requests = 0
            self._successful_executions = 0
            self._failed_executions = 0
            self._cancelled_executions = 0
            self._total_execution_time_ms = 0.0
            self._decisions_by_type.clear()
            self._active_sessions = 0
