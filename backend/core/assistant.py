"""Assistant orchestration for Auralis.

This module contains the assistant boundary only. The assistant validates the
incoming request, asks the planner for an execution plan, sends that plan to
the dispatcher, and returns a structured assistant response. It does not
implement business logic, file operations, AI behavior, or voice handling.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from brain.controller.brain_controller import BrainController
from brain.controller.models import BrainRequest
from .exceptions import DispatchException, PlanningException, ValidationException
from .interfaces import IAssistant, IDispatcher, IPlanner
from .intents import Intent
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
        self._brain_controller = BrainController(logger=self._logger)

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

            # 1. Try executing via the AI Brain Controller pipeline
            brain_req = BrainRequest(
                message=assistant_request.message,
                context={"session_id": session_context.session_id if session_context else None},
                correlation_id=f"exec_{uuid.uuid4().hex[:8]}",
            )
            brain_res = self._brain_controller.process_request(brain_req, self._dispatcher)

            if brain_res.success:
                plan = brain_res.plan
                
                # Normalize target casing for RUN_WORKFLOW to match registry names / legacy tests
                if plan and plan.intent == Intent.RUN_WORKFLOW and plan.target:
                    casing_map = {
                        "START_CODING": "Start Coding",
                        "STUDY": "Study Mode",
                        "MEETING": "Meeting Preparation",
                    }
                    upper_target = plan.target.upper()
                    if upper_target in casing_map:
                        plan.target = casing_map[upper_target]

                # Determine the response string for backward compatibility
                response_str = brain_res.message
                if brain_res.summary and brain_res.summary.records:
                    if len(brain_res.summary.records) == 1:
                        response_str = brain_res.summary.records[0].response or brain_res.message

                result = ExecutionResult(
                    success=True,
                    response=response_str,
                    data=brain_res.summary.model_dump() if brain_res.summary else {},
                    execution_time=brain_res.summary.total_duration if brain_res.summary else 0.0,
                )
                self._logger.info(
                    "Processed assistant request successfully via AI Brain Controller",
                    extra={"goal": brain_res.goal_name},
                )
                return AssistantResponse(
                    response=response_str,
                    plan=plan,
                    result=result,
                )

            # 2. Bypassed or failed, fall back to core planner and dispatcher rules
            self._logger.info("AI Brain pipeline bypassed/failed; executing core planner rules fallback")
            plan = self._planner.create_plan(assistant_request, session_context)
            self._validate_plan(plan)
            result = self._dispatcher.dispatch(plan, session_context)
            self._validate_result(result)
            response = self._build_response(plan, result)
            self._logger.info(
                "Processed assistant request successfully via fallback rules",
                extra={"intent": plan.intent.value, "success": result.success},
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
            intent=Intent.UNKNOWN,
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

        Returns:
            Recognized speech string or empty string.
        """
        from voice.speech_to_text import listen
        res = listen()
        return res if res is not None else ""

    def detect_wake_word(self, text: str) -> dict[str, Any]:
        """Legacy wake-word hook preserved for compatibility.

        Args:
            text: Input command.

        Returns:
            Wake word status.
        """
        from voice.wake_word import detect_wake_word
        return detect_wake_word(text)

    def speak(self, text: str) -> None:
        """Legacy speech hook preserved for compatibility.

        Args:
            text: Response message.
        """
        from voice.text_to_speech import speak
        speak(text)

    def get_voice_listener(self) -> Any:
        """Legacy listener hook preserved for compatibility.

        Returns:
            The continuous voice listener instance.
        """
        from voice.listener import get_listener
        return get_listener()

    def search_files(self, query: str) -> list[dict[str, str]]:
        """Legacy search hook preserved for compatibility.

        Args:
            query: Filename pattern query.

        Returns:
            Matching file dictionary list.
        """
        from capabilities.files.file_operations import search_files
        return search_files(query)

    def get_pending_action(self) -> dict[str, Any] | None:
        """Legacy pending-action hook preserved for compatibility.

        Returns:
            Pending confirmation action metadata or None.
        """
        from capabilities.files.file_operations import get_pending_action
        return get_pending_action()

    def classify_intent(self, command: str) -> str:
        """Legacy intent helper preserved for compatibility.

        Args:
            command: Cleaned voice command.

        Returns:
            Classified intent name string.
        """
        from ai.intent_classifier import classify_intent
        return classify_intent(command)

    def parse_command(self, command: str) -> dict[str, Any]:
        """Legacy parser hook preserved for compatibility.

        Args:
            command: Cleaned voice command.

        Returns:
            Parsed action dictionary.
        """
        from ai.command_parser import parse_command
        return parse_command(command)

    def execute_action(self, parsed_action: dict[str, Any]) -> Any:
        """Legacy execution hook preserved for compatibility.

        Args:
            parsed_action: Parsed action details to run.

        Returns:
            Execution outcome.
        """
        from capabilities.files.file_operations import execute_action
        return execute_action(parsed_action)

    def format_speak_message(self, result: Any, parsed_action: dict[str, Any]) -> str:
        """Legacy formatting hook preserved for compatibility.

        Args:
            result: Command outcome.
            parsed_action: Associated action dictionary.

        Returns:
            Formatted voice response string.
        """
        from utils.helpers import format_speak_message
        return format_speak_message(result, parsed_action)


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