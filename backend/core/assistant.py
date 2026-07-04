"""Assistant orchestration for Auralis.

This module contains the assistant boundary only. The assistant validates the
incoming request, asks the planner for an execution plan, sends that plan to
the dispatcher, and returns a structured assistant response. It does not
implement business logic, file operations, AI behavior, or voice handling.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .exceptions import DispatchException, PlanningException, ValidationException
from .interfaces import IAssistant, IDispatcher, IPlanner
from .models import AssistantRequest, AssistantResponse, ExecutionPlan, ExecutionResult, SessionContext


class AuralisAssistant(IAssistant):
    """Coordinates planning and dispatch for a single assistant request."""

    def __init__(
        self,
        planner: IPlanner,
        dispatcher: IDispatcher,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the assistant with injected collaborators.

        Args:
            planner: The injected planner implementation.
            dispatcher: The injected dispatcher implementation.
            logger: Optional logger used for orchestration diagnostics.
        """

        self._planner = planner
        self._dispatcher = dispatcher
        self._logger = logger or logging.getLogger(__name__)

    def process_request(
        self,
        request: AssistantRequest | str,
        context: SessionContext | str | None = None,
    ) -> AssistantResponse:
        """Processes a request through planner and dispatcher collaborators.

        Args:
            request: The assistant request or legacy session identifier.
            context: The optional session context or legacy command string.

        Returns:
            A structured assistant response, including fallback error details
            when orchestration fails.
        """

        assistant_request, session_context = self._normalize_inputs(request, context)

        try:
            self._validate_request(assistant_request)
            plan = self._planner.create_plan(assistant_request, session_context)
            self._validate_plan(plan)
            result = self._dispatcher.dispatch(plan, session_context)
            self._validate_result(result)
            response = self._build_response(plan, result)
            self._logger.info(
                "Processed assistant request successfully",
                extra={"intent": plan.intent, "success": result.success},
            )
            return response
        except (ValidationException, PlanningException, DispatchException) as exc:
            self._logger.warning(
                "Assistant orchestration failed",
                extra={"error": str(exc)},
            )
            return self._build_failure_response(assistant_request, session_context, str(exc))
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception("Unexpected assistant failure")
            return self._build_failure_response(assistant_request, session_context, str(exc))

    def _normalize_inputs(
        self,
        request: AssistantRequest | str,
        context: SessionContext | str | None,
    ) -> tuple[AssistantRequest, SessionContext | None]:
        """Normalizes both modern and legacy call shapes.

        Args:
            request: The assistant request or legacy session identifier.
            context: The optional session context or legacy command string.

        Returns:
            A normalized assistant request and optional session context.
        """

        if isinstance(request, AssistantRequest):
            if context is None or isinstance(context, SessionContext):
                return request, context

            return request, SessionContext(session_id=request.source)

        if isinstance(context, str):
            legacy_request = AssistantRequest(
                message=context,
                source="legacy",
                timestamp=datetime.now(UTC),
            )
            legacy_context = SessionContext(session_id=request)
            self._logger.debug("Normalized legacy assistant request")
            return legacy_request, legacy_context

        legacy_request = AssistantRequest(
            message="",
            source="legacy",
            timestamp=datetime.now(UTC),
        )
        legacy_context = SessionContext(session_id=str(request))
        return legacy_request, legacy_context

    def _validate_request(self, request: AssistantRequest) -> None:
        """Validates the incoming request payload.

        Args:
            request: The request to validate.

        Raises:
            ValidationException: If the request is not usable.
        """

        if not isinstance(request, AssistantRequest):
            raise ValidationException("Request must be an AssistantRequest instance.")

        if not request.message or not request.message.strip():
            raise ValidationException("Request message cannot be empty.")

        if not request.source or not request.source.strip():
            raise ValidationException("Request source cannot be empty.")

    def _validate_plan(self, plan: ExecutionPlan) -> None:
        """Validates the planner output before dispatch.

        Args:
            plan: The execution plan to validate.

        Raises:
            PlanningException: If the plan is invalid.
        """

        if not isinstance(plan, ExecutionPlan):
            raise PlanningException("Planner must return an ExecutionPlan instance.")

        if not self._planner.validate_plan(plan):
            raise PlanningException("Planner returned an invalid execution plan.")

    def _validate_result(self, result: ExecutionResult) -> None:
        """Validates the dispatcher result.

        Args:
            result: The execution result to validate.

        Raises:
            DispatchException: If the dispatcher returns an invalid result.
        """

        if not isinstance(result, ExecutionResult):
            raise DispatchException("Dispatcher must return an ExecutionResult instance.")

        if result.execution_time < 0:
            raise DispatchException("Execution time cannot be negative.")

    def _build_response(self, plan: ExecutionPlan, result: ExecutionResult) -> AssistantResponse:
        """Builds the success response envelope.

        Args:
            plan: The execution plan that was dispatched.
            result: The resulting execution outcome.

        Returns:
            A structured assistant response.
        """

        response_text = result.response.strip() if result.response else ""
        return AssistantResponse(
            response=response_text,
            plan=plan,
            result=result,
        )

    def _build_failure_response(
        self,
        request: AssistantRequest,
        context: SessionContext | None,
        error_message: str,
    ) -> AssistantResponse:
        """Builds a failure response when orchestration cannot complete.

        Args:
            request: The normalized assistant request.
            context: The optional session context.
            error_message: The failure message to return.

        Returns:
            A structured assistant response with a fallback plan and result.
        """

        fallback_plan = ExecutionPlan(
            intent="UNKNOWN",
            target=None,
            parameters={
                "message": request.message,
                "source": request.source,
                "session_id": context.session_id if context is not None else None,
            },
            confidence=0.0,
        )
        failure_result = ExecutionResult(
            success=False,
            response="",
            data={},
            error=error_message,
            execution_time=0.0,
        )
        return AssistantResponse(
            response=error_message,
            plan=fallback_plan,
            result=failure_result,
        )

    # ------------------------------------------------------------------
    # Compatibility helpers retained for existing API routes.
    # ------------------------------------------------------------------

    def listen_voice(self) -> str:
        """Legacy voice hook preserved for compatibility.

        Raises:
            NotImplementedError: Voice is intentionally out of scope for this phase.
        """

        raise NotImplementedError("Voice interaction is not implemented in this phase.")

    def detect_wake_word(self, text: str) -> dict[str, Any]:
        """Legacy wake-word hook preserved for compatibility.

        Raises:
            NotImplementedError: Voice is intentionally out of scope for this phase.
        """

        raise NotImplementedError("Voice interaction is not implemented in this phase.")

    def speak(self, text: str) -> None:
        """Legacy speech hook preserved for compatibility.

        Raises:
            NotImplementedError: Voice is intentionally out of scope for this phase.
        """

        raise NotImplementedError("Voice interaction is not implemented in this phase.")

    def get_voice_listener(self) -> Any:
        """Legacy listener hook preserved for compatibility.

        Raises:
            NotImplementedError: Voice is intentionally out of scope for this phase.
        """

        raise NotImplementedError("Voice interaction is not implemented in this phase.")

    def search_files(self, query: str) -> list[dict[str, str]]:
        """Legacy search hook preserved for compatibility.

        Raises:
            NotImplementedError: File operations are intentionally out of scope.
        """

        raise NotImplementedError("File search is not implemented in this phase.")

    def get_pending_action(self) -> dict[str, Any] | None:
        """Legacy pending-action hook preserved for compatibility.

        Raises:
            NotImplementedError: Execution state handling is intentionally out of scope.
        """

        raise NotImplementedError("Pending action inspection is not implemented in this phase.")

    def classify_intent(self, command: str) -> str:
        """Legacy intent helper preserved for compatibility.

        Raises:
            NotImplementedError: AI-driven intent classification is intentionally out of scope.
        """

        raise NotImplementedError("Intent classification is not implemented in this phase.")

    def parse_command(self, command: str) -> dict[str, Any]:
        """Legacy parser hook preserved for compatibility.

        Raises:
            NotImplementedError: Parsing is now handled by the planner contract.
        """

        raise NotImplementedError("Command parsing is handled by the planner contract.")

    def execute_action(self, parsed_action: dict[str, Any]) -> Any:
        """Legacy execution hook preserved for compatibility.

        Raises:
            NotImplementedError: Direct execution is intentionally out of scope.
        """

        raise NotImplementedError("Direct execution is not implemented in this phase.")

    def format_speak_message(self, result: Any, parsed_action: dict[str, Any]) -> str:
        """Legacy formatting hook preserved for compatibility.

        Raises:
            NotImplementedError: Voice formatting is intentionally out of scope.
        """

        raise NotImplementedError("Speech formatting is not implemented in this phase.")


Assistant = AuralisAssistant

_assistant_instance: AuralisAssistant | None = None


def set_assistant_instance(assistant: AuralisAssistant) -> None:
    """Registers the assistant singleton used by legacy callers.

    Args:
        assistant: The assistant instance to expose through ``get_assistant``.
    """

    global _assistant_instance
    _assistant_instance = assistant


def get_assistant() -> AuralisAssistant:
    """Returns the configured assistant singleton.

    Returns:
        The configured assistant instance.

    Raises:
        RuntimeError: If no assistant instance has been configured yet.
    """

    if _assistant_instance is None:
        raise RuntimeError(
            "AuralisAssistant has not been configured. Inject Planner and Dispatcher "
            "and register the instance with set_assistant_instance()."
        )

    return _assistant_instance


__all__ = [
    "AuralisAssistant",
    "Assistant",
    "get_assistant",
    "set_assistant_instance",
]