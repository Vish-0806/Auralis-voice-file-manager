"""Workflow capability coordinating registry lookup, validation, and execution."""

from __future__ import annotations

import logging
import time
from typing import Any
from core.interfaces import ICapability
from core.intents import Intent
from core.models import ExecutionPlan, ExecutionResult
from .workflow_parser import WorkflowParser
from .workflow_registry import WorkflowRegistry
from .workflow_validator import WorkflowValidator
from .workflow_executor import WorkflowExecutor


class WorkflowEngine(ICapability):
    """Integrates workflow automation as a system-capable service in Auralis."""

    _SUPPORTED_INTENTS = frozenset({Intent.RUN_WORKFLOW, Intent.LIST_WORKFLOWS})
    _CAPABILITY_NAME = "workflow"

    def __init__(
        self,
        dispatcher: Any = None,
        registry: WorkflowRegistry | None = None,
        parser: WorkflowParser | None = None,
        validator: WorkflowValidator | None = None,
        executor: WorkflowExecutor | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the WorkflowEngine.

        Args:
            dispatcher: ActionDispatcher instance.
            registry: Custom registry mapping.
            parser: Custom parser adapter.
            validator: Custom safety validator.
            executor: Custom step executor.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._dispatcher = dispatcher
        self._registry = registry or WorkflowRegistry(logger=self._logger)
        self._parser = parser or WorkflowParser(logger=self._logger)
        self._validator = validator or WorkflowValidator(logger=self._logger)
        self._executor = executor or WorkflowExecutor(logger=self._logger)

    @property
    def name(self) -> str:
        """Returns registration key."""

        return self._CAPABILITY_NAME

    def set_dispatcher(self, dispatcher: Any) -> None:
        """Sets the dispatcher dynamically if instantiated after capability."""

        self._dispatcher = dispatcher

    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executes a workflow engine action.

        Args:
            action: Action string (Intent).
            arguments: Argument payload.

        Returns:
            Dispatcher compatible dictionary.
        """

        plan = self._build_execution_plan(action, arguments)
        self._validate_plan(plan)
        result = self.execute_plan(plan)
        self._logger.info(
            "Workflow capability action completed",
            extra={
                "action": action,
                "target": plan.target,
                "success": result.success,
                "execution_time_ms": int(result.execution_time * 1000),
            },
        )
        return self._serialize_result(result)

    def execute_plan(self, plan: ExecutionPlan, started_at: float | None = None) -> ExecutionResult:
        """Processes execution plan."""

        execution_started_at = started_at or time.perf_counter()

        if plan.intent == Intent.RUN_WORKFLOW:
            if not plan.target:
                return ExecutionResult(
                    success=False,
                    response="Workflow name target is required.",
                    error="Missing target workflow",
                    execution_time=time.perf_counter() - execution_started_at,
                )

            canonical_name = self._parser.parse_workflow_name(plan.target)
            workflow = self._registry.get_workflow(canonical_name)
            if not workflow:
                return ExecutionResult(
                    success=False,
                    response=f"Workflow '{plan.target}' not found in registry.",
                    error="Registry lookup failed",
                    execution_time=time.perf_counter() - execution_started_at,
                )

            if not self._validator.validate(workflow):
                return ExecutionResult(
                    success=False,
                    response=f"Workflow '{canonical_name}' validation failed (dependencies missing).",
                    error="Validation failure",
                    execution_time=time.perf_counter() - execution_started_at,
                )

            if not self._dispatcher:
                return ExecutionResult(
                    success=False,
                    response="Workflow execution aborted: ActionDispatcher reference is not configured.",
                    error="Dispatcher unconfigured",
                    execution_time=time.perf_counter() - execution_started_at,
                )

            res = self._executor.execute(workflow, self._dispatcher)
            res.execution_time = time.perf_counter() - execution_started_at
            return res

        if plan.intent == Intent.LIST_WORKFLOWS:
            workflows = self._registry.list_workflows()
            lines = ["Available workflows:"]
            for wf in workflows:
                lines.append(f"- {wf.name}: {wf.description}")
            response = "\n".join(lines)
            return ExecutionResult(
                success=True,
                response=response,
                data={"workflows": [wf.name for wf in workflows]},
                execution_time=time.perf_counter() - execution_started_at,
            )

        raise ValueError(f"Unsupported intent: {plan.intent.value}")

    def _build_execution_plan(self, action: str, arguments: dict[str, Any]) -> ExecutionPlan:
        """Converts raw action into plan."""

        try:
            intent = Intent(action)
        except ValueError as exc:
            raise ValueError(f"Unsupported action: {action}") from exc

        parameters = arguments.get("parameters")
        normalized_parameters = parameters if isinstance(parameters, dict) else {}

        return ExecutionPlan(
            intent=intent,
            target=arguments.get("target"),
            parameters=normalized_parameters,
            confidence=1.0,
        )

    def _validate_plan(self, plan: ExecutionPlan) -> None:
        """Ensures intent is supported."""

        if not isinstance(plan, ExecutionPlan):
            raise TypeError("plan must be an ExecutionPlan instance")
        if plan.intent not in self._SUPPORTED_INTENTS:
            raise ValueError(f"Unsupported intent: {plan.intent.value}")

    def _serialize_result(self, result: ExecutionResult) -> dict[str, Any]:
        """Converts result to dispatcher payload."""

        return {
            "response": result.response,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
        }
