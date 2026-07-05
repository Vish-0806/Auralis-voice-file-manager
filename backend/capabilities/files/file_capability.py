"""Foundation file capability for Auralis.

This module provides the first executable file capability surface for the
backend. It validates incoming execution plans, supports the OPEN_FOLDER
intent, and returns a structured core execution result without performing any
operating system interaction yet.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.interfaces import ICapability
from core.intents import Intent
from core.models import ExecutionPlan, ExecutionResult


class FileCapability(ICapability):
    """Handles file-related execution plans for the dispatcher.

    The current foundation only supports OPEN_FOLDER requests. The capability
    validates the incoming plan, builds a non-destructive response, and keeps
    the payload compatible with the dispatcher contract.
    """

    _SUPPORTED_INTENTS: frozenset[Intent] = frozenset({Intent.OPEN_FOLDER})
    _CAPABILITY_NAME = "mock_file"

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the capability.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Returns the dispatcher registration name for this capability."""

        return self._CAPABILITY_NAME

    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executes a supported file action.

        Args:
            action: The requested action name.
            arguments: Structured arguments supplied by the dispatcher.

        Returns:
            A dictionary payload compatible with the dispatcher contract.
        """

        started_at = time.perf_counter()

        try:
            plan = self._build_execution_plan(action, arguments)
            result = self.execute_plan(plan, started_at=started_at)
            return self._serialize_result(result)
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "File capability execution failed",
                extra={"action": action, "arguments": arguments},
            )
            failure = ExecutionResult(
                success=False,
                response="",
                data={"action": action, "arguments": arguments},
                error=str(exc),
                execution_time=time.perf_counter() - started_at,
            )
            return self._serialize_result(failure)

    def execute_plan(
        self,
        plan: ExecutionPlan,
        started_at: float | None = None,
    ) -> ExecutionResult:
        """Executes a validated execution plan.

        Args:
            plan: The execution plan to process.
            started_at: Optional dispatch start timestamp used for timing.

        Returns:
            A structured execution result.

        Raises:
            ValueError: If the plan is invalid or unsupported.
        """

        self._validate_plan(plan)

        execution_started_at = started_at if started_at is not None else time.perf_counter()
        target = self._resolve_target(plan.target)
        message = f"FileCapability received OPEN_FOLDER request for {target}"

        result = ExecutionResult(
            success=True,
            response=message,
            data={
                "intent": plan.intent.value,
                "target": target,
                "parameters": plan.parameters,
            },
            error=None,
            execution_time=time.perf_counter() - execution_started_at,
        )

        self._logger.info(
            "Processed file execution plan",
            extra={
                "intent": plan.intent.value,
                "target": target,
                "success": True,
            },
        )
        return result

    def _build_execution_plan(self, action: str, arguments: dict[str, Any]) -> ExecutionPlan:
        """Builds an execution plan from dispatcher inputs.

        Args:
            action: The requested action name.
            arguments: Dispatcher arguments.

        Returns:
            A normalized execution plan for internal validation.

        Raises:
            ValueError: If the action cannot be mapped to a supported intent.
        """

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
        """Validates the plan before executing it.

        Args:
            plan: The execution plan to validate.

        Raises:
            TypeError: If the plan has the wrong type.
            ValueError: If the intent is unsupported.
        """

        if not isinstance(plan, ExecutionPlan):
            raise TypeError("plan must be an ExecutionPlan instance")

        if plan.intent not in self._SUPPORTED_INTENTS:
            raise ValueError(f"Unsupported intent: {plan.intent.value}")

    def _resolve_target(self, target: str | None) -> str:
        """Resolves a human-readable target string.

        Args:
            target: The requested target from the execution plan.

        Returns:
            A normalized target string for logging and responses.
        """

        if isinstance(target, str) and target.strip():
            return target.strip()

        return "unknown target"

    def _serialize_result(self, result: ExecutionResult) -> dict[str, Any]:
        """Converts a core execution result into a dispatcher payload."""

        return {
            "response": result.response,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
        }


__all__ = ["FileCapability"]