"""Execution Pipeline implementation (Phase 11.9).

Orchestrates full request lifecycle pipeline: Validation -> Security Evaluation ->
Dispatch -> Execution -> Result Collection -> Response Assembly.
"""

import time
import uuid
from typing import List, Optional

from brain.os.integration.exceptions import ExecutionPipelineError
from brain.os.integration.integration_models import (
    ExecutionState,
    ExecutionSummary,
    OperationRequest,
    OperationResponse,
    OperationResult,
)
from brain.os.integration.interfaces import (
    IExecutionPipeline,
    IOperationDispatcher,
    IRequestRouter,
)
from brain.os.integration.operation_dispatcher import OperationDispatcher
from brain.os.integration.request_router import RequestRouter
from brain.os.security.runtime import get_security_runtime
from brain.os.security.security_models import (
    OperationCategory,
    PermissionLevel,
    SecurityContext,
    SecurityDecisionType,
    SecurityRequest,
)
from brain.os.security.security_runtime import SecurityRuntime


class ExecutionPipeline(IExecutionPipeline):
    """Orchestrates full request lifecycle execution pipeline."""

    def __init__(
        self,
        router: Optional[IRequestRouter] = None,
        dispatcher: Optional[IOperationDispatcher] = None,
        security_runtime: Optional[SecurityRuntime] = None,
    ) -> None:
        self._router = router or RequestRouter()
        self._dispatcher = dispatcher or OperationDispatcher()
        self._security_runtime = security_runtime

    def execute_pipeline(self, request: OperationRequest) -> OperationResponse:
        """Execute full request lifecycle pipeline."""
        start_t = time.time()
        stages: List[str] = []
        warnings: List[str] = []
        errors: List[str] = []

        if not request.request_id:
            req_id = f"op_{uuid.uuid4().hex[:8]}"
            request = OperationRequest(
                request_id=req_id,
                target=request.target,
                capability=request.capability,
                action=request.action,
                target_resource=request.target_resource,
                parameters=request.parameters,
                context=request.context,
            )

        # Stage 1: Request Validation
        stages.append(ExecutionState.VALIDATING.value)
        try:
            descriptor = self._router.route(request)
        except Exception as e:
            errors.append(str(e))
            duration = (time.time() - start_t) * 1000.0
            summary = ExecutionSummary(
                request_id=request.request_id,
                state=ExecutionState.FAILED,
                duration_ms=duration,
                stages=stages,
                errors=errors,
            )
            return OperationResponse(
                request_id=request.request_id,
                success=False,
                result=OperationResult(success=False, error=str(e), duration_ms=duration),
                summary=summary,
            )

        # Stage 2: Security Evaluation
        stages.append(ExecutionState.EVALUATING_SECURITY.value)
        sec_rt = self._security_runtime or get_security_runtime()
        sec_req = SecurityRequest(
            request_id=f"sec_{request.request_id}",
            category=OperationCategory(request.target.value) if request.target.value in OperationCategory._value2member_map_ else OperationCategory.SYSTEM,
            operation=descriptor.capability_name,
            target_resource=request.target_resource,
            requested_permission=PermissionLevel.ADMIN if descriptor.requires_admin else PermissionLevel.READ,
            context=SecurityContext(
                user_id=request.context.user_id,
                is_admin=request.context.is_admin,
                session_id=request.context.session_id,
                client_ip=request.context.client_ip,
            ),
            parameters=request.parameters,
        )

        sec_decision = sec_rt.evaluate_request(sec_req)
        sec_dict = sec_decision.model_dump()

        if sec_decision.decision_type == SecurityDecisionType.DENY:
            errors.append(f"Security Policy Denied: {sec_decision.reason}")
            duration = (time.time() - start_t) * 1000.0
            summary = ExecutionSummary(
                request_id=request.request_id,
                state=ExecutionState.FAILED,
                duration_ms=duration,
                stages=stages,
                security_decision=sec_dict,
                errors=errors,
            )
            return OperationResponse(
                request_id=request.request_id,
                success=False,
                result=OperationResult(success=False, error=sec_decision.reason, duration_ms=duration),
                summary=summary,
            )

        if sec_decision.decision_type == SecurityDecisionType.REQUIRE_CONFIRMATION:
            warnings.append("Security Policy requires user confirmation before execution")

        # Stage 3: Dispatch & Execution
        stages.append(ExecutionState.DISPATCHING.value)
        stages.append(ExecutionState.EXECUTING.value)
        try:
            op_result = self._dispatcher.dispatch(request, descriptor)
            stages.append(ExecutionState.COMPLETED.value)
            duration = (time.time() - start_t) * 1000.0

            summary = ExecutionSummary(
                request_id=request.request_id,
                state=ExecutionState.COMPLETED,
                duration_ms=duration,
                stages=stages,
                security_decision=sec_dict,
                warnings=warnings,
            )
            return OperationResponse(
                request_id=request.request_id,
                success=True,
                result=op_result,
                summary=summary,
            )
        except Exception as e:
            errors.append(str(e))
            stages.append(ExecutionState.FAILED.value)
            duration = (time.time() - start_t) * 1000.0

            summary = ExecutionSummary(
                request_id=request.request_id,
                state=ExecutionState.FAILED,
                duration_ms=duration,
                stages=stages,
                security_decision=sec_dict,
                errors=errors,
            )
            return OperationResponse(
                request_id=request.request_id,
                success=False,
                result=OperationResult(success=False, error=str(e), duration_ms=duration),
                summary=summary,
            )
