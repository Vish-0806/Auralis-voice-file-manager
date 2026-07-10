"""Desktop Capability for managing OS applications in Auralis."""

from __future__ import annotations

import logging
import time
from typing import Any

from core.interfaces import ICapability
from core.intents import Intent
from core.models import ExecutionPlan, ExecutionResult

from .application.application_service import ApplicationService
from .windows.window_service import WindowService


class DesktopCapability(ICapability):
    """Handles application management operations (launch, close, restart, list).

    This capability validates incoming execution plans, maps intents to the
    appropriate ApplicationService functions, and returns structured results.
    """

    _SUPPORTED_INTENTS: frozenset[Intent] = frozenset({
        Intent.OPEN_APPLICATION,
        Intent.CLOSE_APPLICATION,
        Intent.RESTART_APPLICATION,
        Intent.LIST_RUNNING_APPLICATIONS,
        Intent.MINIMIZE_WINDOW,
        Intent.MAXIMIZE_WINDOW,
        Intent.RESTORE_WINDOW,
        Intent.FOCUS_WINDOW,
        Intent.CLOSE_WINDOW,
        Intent.SHOW_DESKTOP,
        Intent.LIST_WINDOWS,
    })
    _CAPABILITY_NAME = "desktop"

    def __init__(
        self,
        application_service: ApplicationService | None = None,
        window_service: WindowService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the DesktopCapability.

        Args:
            application_service: Preconfigured ApplicationService instance.
            window_service: Preconfigured WindowService instance.
            logger: Optional logger for capability diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._application_service = application_service or ApplicationService(logger=self._logger)
        self._window_service = window_service or WindowService(logger=self._logger)

    @property
    def name(self) -> str:
        """Returns the stable registration name of this capability."""

        return self._CAPABILITY_NAME

    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Executes a supported desktop action.

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
        except Exception as exc:
            self._logger.exception(
                "Desktop capability execution failed",
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

        intent = plan.intent
        target = plan.target

        if intent == Intent.OPEN_APPLICATION:
            if not target:
                raise ValueError("An application target name is required to open an application.")
            pid = self._application_service.launch_application(target)
            response = f"Successfully launched {target} (PID: {pid})."
            data = {"pid": pid, "application": target}
            return ExecutionResult(
                success=True,
                response=response,
                data=data,
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.CLOSE_APPLICATION:
            if not target:
                raise ValueError("An application target name is required to close an application.")
            closed = self._application_service.close_application(target)
            if closed:
                response = f"Successfully closed {target}."
            else:
                response = f"No running instances of {target} were found."
            return ExecutionResult(
                success=True,
                response=response,
                data={"application": target, "terminated": closed},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.RESTART_APPLICATION:
            if not target:
                raise ValueError("An application target name is required to restart an application.")
            pid = self._application_service.restart_application(target)
            response = f"Successfully restarted {target} (New PID: {pid})."
            return ExecutionResult(
                success=True,
                response=response,
                data={"application": target, "pid": pid},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.LIST_RUNNING_APPLICATIONS:
            apps = self._application_service.list_running_applications()
            running = [app.name for app in apps if app.is_running]
            if running:
                response = f"Currently running applications: {', '.join(running)}."
            else:
                response = "No monitored applications are currently running."
            return ExecutionResult(
                success=True,
                response=response,
                data={"applications": [app.model_dump() for app in apps]},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.MINIMIZE_WINDOW:
            success = self._window_service.minimize_window(target)
            if success:
                response = f"Successfully minimized window '{target or 'active'}'."
            else:
                response = f"Could not minimize window '{target or 'active'}'."
            return ExecutionResult(
                success=success,
                response=response,
                data={"target": target},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.MAXIMIZE_WINDOW:
            success = self._window_service.maximize_window(target)
            if success:
                response = f"Successfully maximized window '{target or 'active'}'."
            else:
                response = f"Could not maximize window '{target or 'active'}'."
            return ExecutionResult(
                success=success,
                response=response,
                data={"target": target},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.RESTORE_WINDOW:
            success = self._window_service.restore_window(target)
            if success:
                response = f"Successfully restored window '{target or 'active'}'."
            else:
                response = f"Could not restore window '{target or 'active'}'."
            return ExecutionResult(
                success=success,
                response=response,
                data={"target": target},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.FOCUS_WINDOW:
            success = self._window_service.focus_window(target)
            if success:
                response = f"Successfully focused window '{target or 'active'}'."
            else:
                response = f"Could not focus window '{target or 'active'}'."
            return ExecutionResult(
                success=success,
                response=response,
                data={"target": target},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.CLOSE_WINDOW:
            success = self._window_service.close_window(target)
            if success:
                response = f"Successfully closed window '{target or 'active'}'."
            else:
                response = f"Could not close window '{target or 'active'}'."
            return ExecutionResult(
                success=success,
                response=response,
                data={"target": target},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.SHOW_DESKTOP:
            self._window_service.show_desktop()
            return ExecutionResult(
                success=True,
                response="Desktop shown.",
                data={},
                execution_time=time.perf_counter() - execution_started_at,
            )

        if intent == Intent.LIST_WINDOWS:
            wins = self._window_service.list_windows()
            open_wins = [w.title for w in wins]
            if open_wins:
                response = f"Currently open windows: {', '.join(open_wins)}."
            else:
                response = "No open application windows were found."
            return ExecutionResult(
                success=True,
                response=response,
                data={"windows": [w.model_dump() for w in wins]},
                execution_time=time.perf_counter() - execution_started_at,
            )

        raise ValueError(f"Unsupported intent: {intent.value}")

    def _build_execution_plan(self, action: str, arguments: dict[str, Any]) -> ExecutionPlan:
        """Builds an execution plan from dispatcher inputs."""

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
        """Validates the plan before execution."""

        if not isinstance(plan, ExecutionPlan):
            raise TypeError("plan must be an ExecutionPlan instance")

        if plan.intent not in self._SUPPORTED_INTENTS:
            raise ValueError(f"Unsupported intent: {plan.intent.value}")

    def _serialize_result(self, result: ExecutionResult) -> dict[str, Any]:
        """Converts a core execution result into a dispatcher payload."""

        return {
            "response": result.response,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
        }
