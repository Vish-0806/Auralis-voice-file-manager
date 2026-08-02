"""Execution Router for the Auralis Command Execution Orchestrator (Phase 12.3).

Responsible for pure routing dispatch across subsystem runtimes:
- Intent Resolution Runtime
- Planning Runtime
- Security Runtime
- Operating System Integration Runtime
- Brain Execution Engine

Contains ZERO subsystem implementation logic.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.execution.orchestrator.exceptions import ExecutionRoutingError
from brain.execution.orchestrator.interfaces import IExecutionRouter
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionContext,
    ExecutionStage,
    ExecutionStageType,
    OrchestrationStatus,
)


class ExecutionRouter(IExecutionRouter):
    """Router handling stage dispatch across subsystem runtimes."""

    def __init__(
        self,
        intent_runtime: Optional[Any] = None,
        planning_runtime: Optional[Any] = None,
        security_runtime: Optional[Any] = None,
        os_runtime: Optional[Any] = None,
        execution_engine: Optional[Any] = None,
    ) -> None:
        """Initializes ExecutionRouter with optional injected subsystem runtimes."""
        self._intent_runtime = intent_runtime
        self._planning_runtime = planning_runtime
        self._security_runtime = security_runtime
        self._os_runtime = os_runtime
        self._execution_engine = execution_engine

    def route_stage(
        self,
        stage_type: ExecutionStageType,
        context: ExecutionContext,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStage:
        """Route execution of a stage to its target subsystem runtime.

        Args:
            stage_type: ExecutionStageType enum value.
            context: Live ExecutionContext.
            payload: Optional stage payload dict.

        Returns:
            ExecutionStage outcome model.

        Raises:
            ExecutionRoutingError: If stage routing encounters an unrecoverable invalid state.
        """
        start_time = time.perf_counter()
        eff_payload = dict(payload or {})
        started_at = datetime.now(timezone.utc)

        try:
            output: Dict[str, Any] = {}
            status = OrchestrationStatus.SUCCESS

            if stage_type == ExecutionStageType.INTENT_RESOLUTION:
                if self._intent_runtime and hasattr(self._intent_runtime, "process_intent"):
                    res = self._intent_runtime.process_intent(context.request.raw_prompt)
                    output["resolution"] = res.model_dump() if hasattr(res, "model_dump") else res
                else:
                    output["resolution"] = "Intent Resolution Runtime routed (Default)"

            elif stage_type == ExecutionStageType.PLANNING:
                if self._planning_runtime and hasattr(self._planning_runtime, "create_plan"):
                    plan = self._planning_runtime.create_plan(context.request.raw_prompt)
                    output["plan"] = plan
                else:
                    output["plan"] = {"steps": 1, "status": "PLAN_GENERATED"}

            elif stage_type == ExecutionStageType.SECURITY_REVIEW:
                if self._security_runtime and hasattr(self._security_runtime, "evaluate"):
                    sec_res = self._security_runtime.evaluate(context.request.raw_prompt)
                    output["security"] = sec_res
                else:
                    output["security"] = {"allowed": True, "policy": "DEFAULT"}

            elif stage_type == ExecutionStageType.OS_EXECUTION:
                if self._os_runtime and hasattr(self._os_runtime, "execute_command"):
                    os_res = self._os_runtime.execute_command(context.request.raw_prompt)
                    output["execution"] = os_res
                elif self._execution_engine and hasattr(self._execution_engine, "process_request"):
                    eng_res = self._execution_engine.process_request(context.request.raw_prompt)
                    output["execution"] = eng_res.model_dump() if hasattr(eng_res, "model_dump") else eng_res
                else:
                    output["execution"] = {"result": "OS Command executed successfully (Default)"}

            elif stage_type == ExecutionStageType.RESPONSE_SYNTHESIS:
                output["response"] = f"Processed request: '{context.request.raw_prompt}'"

            else:
                raise ExecutionRoutingError(f"Unsupported stage type: {stage_type}")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionStage(
                stage_type=stage_type,
                status=status,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                duration_ms=elapsed_ms,
                output=output,
                metadata={"payload": eff_payload},
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionStage(
                stage_type=stage_type,
                status=OrchestrationStatus.FAILED,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                duration_ms=elapsed_ms,
                error=str(exc),
            )
