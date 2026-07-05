"""Dispatcher contracts and mock execution routing for Auralis.

This module implements the dispatcher boundary only. It receives an execution
plan, selects the appropriate capability, executes that capability, and wraps
the outcome in a structured ExecutionResult. No real OS interaction occurs
here; the temporary mock capability is used for phase validation.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .exceptions import DispatchException, ValidationException
from .interfaces import ICapability, IDispatcher
from .intents import Intent
from .models import ExecutionPlan, ExecutionResult


class ActionDispatcher(IDispatcher):
    """Routes execution plans to registered capabilities."""

    _SUPPORTED_INTENTS: set[Intent] = {
        Intent.OPEN_FOLDER,
        Intent.OPEN_FILE,
        Intent.SEARCH_FILE,
        Intent.LIST_DIRECTORY,
        Intent.CREATE_FOLDER,
        Intent.DELETE_FOLDER,
        Intent.UNKNOWN,
    }

    def __init__(
        self,
        capabilities: dict[str, ICapability] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the dispatcher.

        Args:
            capabilities: Optional pre-registered capability instances.
            logger: Optional logger for dispatch diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._capabilities: dict[str, ICapability] = capabilities.copy() if capabilities else {}

        if not self._capabilities:
            from capabilities.mock.mock_file import MockFileCapability

            mock_capability = MockFileCapability()
            self.register_capability(mock_capability)

    def register_capability(self, capability: ICapability) -> None:
        """Registers a capability by its stable name.

        Args:
            capability: The capability instance to register.

        Raises:
            ValidationException: If the capability is invalid.
        """

        if not isinstance(capability, ICapability):
            raise ValidationException("Capability must implement ICapability.")

        name = capability.name.strip()
        if not name:
            raise ValidationException("Capability name cannot be empty.")

        self._capabilities[name] = capability
        self._logger.debug("Registered capability", extra={"capability": name})

    def dispatch(self, plan: ExecutionPlan, context: Any | None = None) -> ExecutionResult:
        """Executes a plan through the correct capability.

        Args:
            plan: The execution plan to dispatch.
            context: Optional session context retained for future extensibility.

        Returns:
            A structured execution result.
        """

        started_at = time.perf_counter()

        try:
            self._validate_plan(plan)

            if plan.intent == Intent.UNKNOWN:
                return self._build_failure_result(
                    intent=plan.intent,
                    started_at=started_at,
                    error_message=f"Unsupported intent: {plan.intent.value}",
                )

            capability = self._resolve_capability(plan.intent)
            response_text = self._execute_capability(capability, plan)
            execution_time = time.perf_counter() - started_at

            result = ExecutionResult(
                success=True,
                response=response_text,
                data={
                    "intent": plan.intent.value,
                    "target": plan.target,
                    "capability": capability.name,
                    "parameters": plan.parameters,
                },
                error=None,
                execution_time=execution_time,
            )

            self._logger.info(
                "Dispatched execution plan",
                extra={
                    "intent": plan.intent.value,
                    "capability": capability.name,
                    "success": True,
                },
            )
            return result
        except (DispatchException, ValidationException) as exc:
            return self._build_failure_result(
                intent=getattr(plan, "intent", None),
                started_at=started_at,
                error_message=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception("Dispatch failed", extra={"intent": getattr(plan, "intent", None)})
            return self._build_failure_result(
                intent=getattr(plan, "intent", None),
                started_at=started_at,
                error_message=str(exc),
            )

    def _validate_plan(self, plan: ExecutionPlan) -> None:
        """Validates the execution plan before routing.

        Args:
            plan: The execution plan to validate.

        Raises:
            ValidationException: If the plan is invalid.
        """

        if not isinstance(plan, ExecutionPlan):
            raise ValidationException("Plan must be an ExecutionPlan instance.")

        if plan.intent not in self._SUPPORTED_INTENTS:
            raise ValidationException(f"Unsupported intent: {plan.intent.value}")

    def _resolve_capability(self, intent: Intent) -> ICapability:
        """Resolves the capability for a given intent.

        Args:
            intent: The intent to resolve.

        Returns:
            The matching capability instance.

        Raises:
            DispatchException: If no capability is registered for the intent.
        """

        capability_name = self._intent_to_capability_name(intent)
        capability = self._capabilities.get(capability_name)
        if capability is None:
            raise DispatchException(f"No capability registered for intent: {intent}")

        return capability

    def _intent_to_capability_name(self, intent: Intent) -> str:
        """Maps an intent to the expected capability name."""

        return "mock_file"

    def _execute_capability(self, capability: ICapability, plan: ExecutionPlan) -> str:
        """Executes the capability and converts the output into a response string.

        Args:
            capability: The capability to invoke.
            plan: The execution plan being processed.

        Returns:
            A human-readable response string.

        Raises:
            DispatchException: If capability execution returns an invalid payload.
        """

        payload = capability.execute(
            action=plan.intent.value,
            arguments={
                "target": plan.target,
                "parameters": plan.parameters,
            },
        )

        if not isinstance(payload, dict):
            raise DispatchException("Capability must return a dictionary payload.")

        response = payload.get("response")
        if not isinstance(response, str) or not response.strip():
            raise DispatchException("Capability response must be a non-empty string.")

        return response.strip()

    def _build_failure_result(
        self,
        intent: Intent | None,
        started_at: float,
        error_message: str,
    ) -> ExecutionResult:
        """Builds a structured failure result for routing or execution errors.

        Args:
            intent: The plan intent that failed.
            started_at: The dispatch start timestamp.
            error_message: The failure description.

        Returns:
            A structured ExecutionResult describing the failure.
        """

        execution_time = time.perf_counter() - started_at
        return ExecutionResult(
            success=False,
            response="",
            data={"intent": intent.value if intent is not None else None},
            error=error_message,
            execution_time=execution_time,
        )


__all__ = ["ActionDispatcher", "ExecutionResult"]