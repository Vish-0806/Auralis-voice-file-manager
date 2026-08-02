"""Execution Router for the Auralis Execution Runtime Integration (Phase 12.9).

Routes incoming IntegrationRequest objects to the appropriate ExecutionTarget based on context and capability analysis.
"""

from typing import Optional

from brain.execution.integration.exceptions import RoutingError
from brain.execution.integration.interfaces import ICapabilityRegistry, IExecutionRouter
from brain.execution.integration.integration_models import ExecutionTarget, IntegrationRequest


class ExecutionRouter(IExecutionRouter):
    """Router determining the target subsystem for an incoming IntegrationRequest."""

    def __init__(self, capability_registry: Optional[ICapabilityRegistry] = None) -> None:
        """Initializes ExecutionRouter with optional capability registry."""
        self._capability_registry = capability_registry

    def route_request(self, request: IntegrationRequest) -> ExecutionTarget:
        """Route an IntegrationRequest to an ExecutionTarget.

        Args:
            request: IntegrationRequest model.

        Returns:
            ExecutionTarget enum.

        Raises:
            RoutingError: If request is invalid.
        """
        if not request:
            raise RoutingError("Cannot route null or empty IntegrationRequest")

        # 1. Check explicit target override in request metadata or context
        override_target = request.metadata.get("target") or request.context_data.get("target")
        if override_target:
            try:
                return ExecutionTarget(override_target)
            except ValueError:
                pass

        user_txt = request.user_input.lower().strip()

        # 2. Text keyword analysis for subsystem routing
        if any(k in user_txt for k in ["workflow", "pipeline", "multi-step", "then"]):
            return ExecutionTarget.WORKFLOW_ENGINE

        if any(k in user_txt for k in ["task", "background", "long-running", "job"]):
            return ExecutionTarget.TASK_RUNTIME

        if any(k in user_txt for k in ["schedule", "cron", "automation", "trigger", "every"]):
            return ExecutionTarget.AUTOMATION_RUNTIME

        if any(k in user_txt for k in ["intent", "classify", "recognize", "extract"]):
            return ExecutionTarget.INTENT_ENGINE

        # 3. Default routing target
        return ExecutionTarget.COMMAND_ORCHESTRATOR
