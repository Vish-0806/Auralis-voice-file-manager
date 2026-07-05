"""File capability for Auralis.

This module validates incoming execution plans, resolves supported user folder
targets, searches supported folders, opens the resolved folder in Windows
Explorer, and returns a structured execution result for the dispatcher.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from core.interfaces import ICapability
from core.intents import Intent
from core.models import ExecutionPlan, ExecutionResult

from .path_resolver import PathResolver
from .search_engine import SearchEngine


class FileCapability(ICapability):
    """Handles file-related execution plans for the dispatcher.

    The capability currently supports folder opening and recursive file search.
    It validates the incoming plan, resolves the target path, searches known
    folders, opens folders using ``os.startfile()``, and keeps the payload
    compatible with the dispatcher contract.
    """

    _SUPPORTED_INTENTS: frozenset[Intent] = frozenset({Intent.OPEN_FOLDER, Intent.SEARCH_FILE})
    _CAPABILITY_NAME = "mock_file"

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the capability.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._path_resolver = PathResolver(logger=self._logger)
        self._search_engine = SearchEngine(logger=self._logger, path_resolver=self._path_resolver)

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
            OSError: If the folder cannot be opened.
        """

        self._validate_plan(plan)

        execution_started_at = started_at if started_at is not None else time.perf_counter()
        target = self._resolve_target(plan.target)

        if plan.intent == Intent.SEARCH_FILE:
            return self._search_files(plan, target, execution_started_at)

        resolved_path = self._path_resolver.resolve(target)
        if resolved_path is None:
            error_message = f"Unable to resolve folder path for {target}"
            self._logger.warning(
                "Folder resolution failed",
                extra={"intent": plan.intent.value, "target": target},
            )
            return ExecutionResult(
                success=False,
                response="",
                data={
                    "intent": plan.intent.value,
                    "target": target,
                    "parameters": plan.parameters,
                },
                error=error_message,
                execution_time=time.perf_counter() - execution_started_at,
            )

        self._open_folder(resolved_path)
        message = f"FileCapability received OPEN_FOLDER request for {target}"

        result = ExecutionResult(
            success=True,
            response=message,
            data={
                "intent": plan.intent.value,
                "target": target,
                "resolved_path": resolved_path,
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

    def _search_files(
        self,
        plan: ExecutionPlan,
        target: str,
        execution_started_at: float,
    ) -> ExecutionResult:
        """Executes a recursive search across the supported file scopes."""

        try:
            matches = self._search_engine.search(target)
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "File search failed",
                extra={"intent": plan.intent.value, "query": target},
            )
            return ExecutionResult(
                success=False,
                response="",
                data={
                    "intent": plan.intent.value,
                    "target": target,
                    "parameters": plan.parameters,
                },
                error=str(exc),
                execution_time=time.perf_counter() - execution_started_at,
            )

        if matches:
            response = f"Found {len(matches)} matching path(s) for {target}: {', '.join(matches)}"
        else:
            response = f"No files or folders found matching {target}"

        result = ExecutionResult(
            success=True,
            response=response,
            data={
                "intent": plan.intent.value,
                "target": target,
                "matches": matches,
                "match_count": len(matches),
                "parameters": plan.parameters,
            },
            error=None,
            execution_time=time.perf_counter() - execution_started_at,
        )

        self._logger.info(
            "Processed file search plan",
            extra={
                "intent": plan.intent.value,
                "query": target,
                "match_count": len(matches),
                "success": True,
            },
        )
        return result

    def _open_folder(self, resolved_path: str) -> None:
        """Opens the resolved folder in the native Windows file explorer.

        Args:
            resolved_path: The absolute path to the folder to open.

        Raises:
            OSError: If ``os.startfile`` is unavailable or the launch fails.
        """

        if not hasattr(os, "startfile"):
            raise OSError("os.startfile is not available on this platform")

        try:
            os.startfile(resolved_path)
        except OSError as exc:
            self._logger.exception(
                "Failed to open folder",
                extra={"path": resolved_path},
            )
            raise OSError(f"Failed to open folder: {resolved_path}") from exc

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