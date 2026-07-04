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
from .models import ExecutionPlan, ExecutionResult


class ActionDispatcher(IDispatcher):
    """Routes execution plans to registered capabilities."""

    _SUPPORTED_INTENTS: set[str] = {
        "OPEN_FOLDER",
        "OPEN_FILE",
        "SEARCH_FILE",
        "LIST_DIRECTORY",
        "UNKNOWN",
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

            if plan.intent == "UNKNOWN":
                return self._build_failure_result(
                    intent=plan.intent,
                    started_at=started_at,
                    error_message="Unsupported intent: UNKNOWN",
                )

            capability = self._resolve_capability(plan.intent)
            response_text = self._execute_capability(capability, plan)
            execution_time = time.perf_counter() - started_at

            result = ExecutionResult(
                success=True,
                response=response_text,
                data={
                    "intent": plan.intent,
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
                    "intent": plan.intent,
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
            raise ValidationException(f"Unsupported intent: {plan.intent}")

        if not plan.intent.strip():
            raise ValidationException("Plan intent cannot be empty.")

    def _resolve_capability(self, intent: str) -> ICapability:
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

    def _intent_to_capability_name(self, intent: str) -> str:
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
            action=plan.intent,
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
        intent: str | None,
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
            data={"intent": intent},
            error=error_message,
            execution_time=execution_time,
        )


__all__ = ["ActionDispatcher", "ExecutionResult"]