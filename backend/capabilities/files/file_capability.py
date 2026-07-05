"""File capability for Auralis.

This module validates incoming execution plans, resolves supported user folder
targets, searches supported folders, transfers files, renames items, deletes
items into the Recycle Bin, opens the resolved folder in Windows Explorer,
and returns a structured execution result for the dispatcher.
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
from .file_operation_service import FileOperationService
from .transfer_service import TransferService
from .folder_service import FolderService


class FileCapability(ICapability):
    """Handles file-related execution plans for the dispatcher.

    The capability currently supports folder opening, recursive file search,
    file transfer, rename, and delete operations. It validates the incoming
    plan, resolves the target path, searches known folders, transfers files,
    renames items, moves items to the Recycle Bin, opens folders using
    ``os.startfile()``, and keeps the payload compatible with the dispatcher
    contract.
    """

    _SUPPORTED_INTENTS: frozenset[Intent] = frozenset({
        Intent.OPEN_FOLDER,
        Intent.SEARCH_FILE,
        Intent.CREATE_FOLDER,
        Intent.DELETE_FOLDER,
    })
    _CAPABILITY_NAME = "mock_file"

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the capability.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._path_resolver = PathResolver(logger=self._logger)
        self._search_engine = SearchEngine(logger=self._logger, path_resolver=self._path_resolver)
        self._file_operation_service = FileOperationService(logger=self._logger)
        self._transfer_service = TransferService(logger=self._logger)
        self._folder_service = FolderService(logger=self._logger)

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
            if action in {"RENAME_FILE", "RENAME_FOLDER"}:
                result = self._handle_rename_action(action, arguments, started_at)
                return self._serialize_result(result)

            if action in {"DELETE_FILE", "DELETE_FOLDER"}:
                result = self._handle_delete_action(action, arguments, started_at)
                return self._serialize_result(result)

            if action in {"COPY_FILE", "MOVE_FILE"}:
                result = self._handle_transfer_action(action, arguments, started_at)
                return self._serialize_result(result)

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

        if plan.intent == Intent.CREATE_FOLDER:
            folder_name = plan.parameters.get("folder_name") or target
            destination_folder = plan.parameters.get("destination_folder")

            if destination_folder:
                resolved_dest = self._path_resolver.resolve(destination_folder)
                if resolved_dest is None:
                    return ExecutionResult(
                        success=False,
                        response="",
                        data={
                            "intent": plan.intent.value,
                            "target": target,
                            "parameters": plan.parameters,
                        },
                        error=f"Unable to resolve destination folder '{destination_folder}'",
                        execution_time=time.perf_counter() - execution_started_at,
                    )
            else:
                from pathlib import Path
                resolved_dest = str(Path.home())

            res = self._folder_service.create_folder(folder_name, resolved_dest)
            success = res.get("status") == "success"
            return ExecutionResult(
                success=success,
                response=res.get("message", "") if success else "",
                data={
                    "intent": plan.intent.value,
                    "target": target,
                    "folder_name": folder_name,
                    "destination": res.get("path"),
                    "operation": "create_folder",
                    "parameters": plan.parameters,
                },
                error=res.get("message") if not success else None,
                execution_time=time.perf_counter() - execution_started_at,
            )

        if plan.intent == Intent.DELETE_FOLDER:
            folder_hint = plan.parameters.get("folder_name") or target
            resolved_path = self._resolve_source_path(folder_hint, expect_directory=True)
            if resolved_path is None:
                return ExecutionResult(
                    success=False,
                    response="",
                    data={
                        "intent": plan.intent.value,
                        "target": target,
                        "parameters": plan.parameters,
                    },
                    error=f"Unable to locate folder '{folder_hint}'",
                    execution_time=time.perf_counter() - execution_started_at,
                )

            res = self._folder_service.delete_folder(resolved_path)
            success = res.get("status") == "success"
            return ExecutionResult(
                success=success,
                response=res.get("message", "") if success else "",
                data={
                    "intent": plan.intent.value,
                    "target": target,
                    "resolved_path": resolved_path,
                    "operation": "delete_folder",
                    "parameters": plan.parameters,
                },
                error=res.get("message") if not success else None,
                execution_time=time.perf_counter() - execution_started_at,
            )

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

    def _handle_transfer_action(
        self,
        action: str,
        arguments: dict[str, Any],
        started_at: float,
    ) -> ExecutionResult:
        """Handles copy and move requests from the legacy action interface."""

        operation = "copy" if action == "COPY_FILE" else "move"
        source_hint, destination_hint = self._extract_transfer_arguments(arguments)

        source_path = self._resolve_source_path(source_hint)
        if source_path is None:
            return self._build_transfer_failure(
                operation=operation,
                target=source_hint,
                message=f"Unable to locate source file '{source_hint}'",
                started_at=started_at,
            )

        destination_path = self._resolve_destination_path(destination_hint)
        if destination_path is None:
            return self._build_transfer_failure(
                operation=operation,
                target=destination_hint,
                message=f"Unable to resolve destination folder '{destination_hint}'",
                started_at=started_at,
            )

        try:
            transfer_result = (
                self._transfer_service.copy_file(source_path, destination_path)
                if operation == "copy"
                else self._transfer_service.move_file(source_path, destination_path)
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "File transfer failed",
                extra={"operation": operation, "source": source_path, "destination": destination_path},
            )
            return self._build_transfer_failure(
                operation=operation,
                target=source_hint,
                message=str(exc),
                started_at=started_at,
            )

        success = transfer_result.get("status") == "success"
        message = transfer_result.get("message", "")
        error_message = transfer_result.get("error")

        return ExecutionResult(
            success=success,
            response=message if success else "",
            data={
                "intent": action,
                "source": source_path,
                "destination": transfer_result.get("destination", destination_path),
                "operation": operation,
                "parameters": arguments.get("parameters", {}),
            },
            error=error_message if not success else None,
            execution_time=time.perf_counter() - started_at,
        )

    def _handle_rename_action(
        self,
        action: str,
        arguments: dict[str, Any],
        started_at: float,
    ) -> ExecutionResult:
        """Handles file and folder rename requests."""

        target_hint, new_name = self._extract_rename_arguments(arguments)
        source_path = self._resolve_source_path(target_hint, expect_directory=action.endswith("_FOLDER"))
        if source_path is None:
            return self._build_operation_failure(
                operation="rename",
                target=target_hint,
                message=f"Unable to locate target '{target_hint}'",
                started_at=started_at,
            )

        if not new_name:
            return self._build_operation_failure(
                operation="rename",
                target=target_hint,
                message="A valid new name is required for rename operations.",
                started_at=started_at,
            )

        try:
            operation_result = self._file_operation_service.rename(source_path, new_name)
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "Rename failed",
                extra={"source": source_path, "new_name": new_name},
            )
            return self._build_operation_failure(
                operation="rename",
                target=target_hint,
                message=str(exc),
                started_at=started_at,
            )

        success = operation_result.get("status") == "success"
        return ExecutionResult(
            success=success,
            response=operation_result.get("message", "") if success else "",
            data={
                "intent": action,
                "source": source_path,
                "destination": operation_result.get("destination"),
                "operation": "rename",
                "parameters": arguments.get("parameters", {}),
            },
            error=operation_result.get("error") if not success else None,
            execution_time=time.perf_counter() - started_at,
        )

    def _handle_delete_action(
        self,
        action: str,
        arguments: dict[str, Any],
        started_at: float,
    ) -> ExecutionResult:
        """Handles file and folder delete requests."""

        target_hint = self._extract_delete_target(arguments)
        target_path = self._resolve_source_path(target_hint, expect_directory=action.endswith("_FOLDER"))
        if target_path is None:
            return self._build_operation_failure(
                operation="delete",
                target=target_hint,
                message=f"Unable to locate target '{target_hint}'",
                started_at=started_at,
            )

        try:
            if action == "DELETE_FOLDER":
                operation_result = self._folder_service.delete_folder(target_path)
            else:
                operation_result = self._file_operation_service.delete(target_path)
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "Delete failed",
                extra={"target": target_path},
            )
            return self._build_operation_failure(
                operation="delete",
                target=target_hint,
                message=str(exc),
                started_at=started_at,
            )

        success = operation_result.get("status") == "success"
        return ExecutionResult(
            success=success,
            response=operation_result.get("message", "") if success else "",
            data={
                "intent": action,
                "target": target_path,
                "operation": "delete",
                "parameters": arguments.get("parameters", {}),
            },
            error=operation_result.get("error") if not success else None,
            execution_time=time.perf_counter() - started_at,
        )

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

    def _extract_transfer_arguments(self, arguments: dict[str, Any]) -> tuple[str, str]:
        """Extracts source and destination hints from dispatcher arguments."""

        parameters = arguments.get("parameters") if isinstance(arguments.get("parameters"), dict) else {}

        source_hint = self._resolve_target(
            arguments.get("target") or parameters.get("source") or parameters.get("target")
        )
        destination_hint = self._resolve_target(
            parameters.get("destination") or parameters.get("location") or parameters.get("dest")
        )
        return source_hint, destination_hint

    def _extract_rename_arguments(self, arguments: dict[str, Any]) -> tuple[str, str]:
        """Extracts rename source and new name hints from dispatcher arguments."""

        parameters = arguments.get("parameters") if isinstance(arguments.get("parameters"), dict) else {}
        target_hint = self._resolve_target(
            arguments.get("target") or parameters.get("target") or parameters.get("source")
        )
        new_name = self._resolve_target(
            parameters.get("new_name") or parameters.get("name") or parameters.get("destination")
        )
        return target_hint, new_name

    def _extract_delete_target(self, arguments: dict[str, Any]) -> str:
        """Extracts the delete target hint from dispatcher arguments."""

        parameters = arguments.get("parameters") if isinstance(arguments.get("parameters"), dict) else {}
        return self._resolve_target(arguments.get("target") or parameters.get("target") or parameters.get("source"))

    def _resolve_source_path(self, source_hint: str, expect_directory: bool = False) -> str | None:
        """Resolves a source path using direct lookup and search.

        Args:
            source_hint: The user-provided source name or path.
            expect_directory: Whether the caller expects a folder target.

        Returns:
            The resolved absolute path, or ``None`` when it cannot be
            resolved uniquely.
        """

        if not source_hint or source_hint == "unknown target":
            return None

        if os.path.exists(source_hint) and os.path.isfile(source_hint):
            return os.path.abspath(source_hint)

        matches = self._search_engine.search(source_hint)
        if not matches:
            return None

        exact_matches = [match for match in matches if os.path.basename(match).lower() == source_hint.lower()]

        if expect_directory:
            directory_matches = [match for match in exact_matches if os.path.isdir(match)] or [
                match for match in matches if os.path.isdir(match)
            ]

            if len(directory_matches) == 1:
                return os.path.abspath(directory_matches[0])

            if len(directory_matches) > 1:
                self._logger.warning(
                    "Multiple folder matches found",
                    extra={"source_hint": source_hint, "matches": directory_matches},
                )
                return None

            return None

        file_matches = [match for match in exact_matches if os.path.isfile(match)] or [
            match for match in matches if os.path.isfile(match)
        ]

        if len(file_matches) == 1:
            return os.path.abspath(file_matches[0])

        if len(file_matches) > 1:
            self._logger.warning(
                "Multiple source matches found",
                extra={"source_hint": source_hint, "matches": file_matches},
            )
            return None

        return None

    def _resolve_destination_path(self, destination_hint: str) -> str | None:
        """Resolves the destination folder path using the path resolver."""

        if not destination_hint or destination_hint == "unknown target":
            return None

        resolved_path = self._path_resolver.resolve(destination_hint)
        if resolved_path is not None:
            return resolved_path

        if os.path.exists(destination_hint) and os.path.isdir(destination_hint):
            return os.path.abspath(destination_hint)

        return None

    def _build_transfer_failure(
        self,
        operation: str,
        target: str,
        message: str,
        started_at: float,
    ) -> ExecutionResult:
        """Builds a failure result for transfer operations."""

        self._logger.warning(
            "File transfer validation failed",
            extra={"operation": operation, "target": target, "message": message},
        )
        return ExecutionResult(
            success=False,
            response="",
            data={"operation": operation, "target": target},
            error=message,
            execution_time=time.perf_counter() - started_at,
        )

    def _build_operation_failure(
        self,
        operation: str,
        target: str,
        message: str,
        started_at: float,
    ) -> ExecutionResult:
        """Builds a failure result for rename and delete operations."""

        self._logger.warning(
            "File operation validation failed",
            extra={"operation": operation, "target": target, "message": message},
        )
        return ExecutionResult(
            success=False,
            response="",
            data={"operation": operation, "target": target},
            error=message,
            execution_time=time.perf_counter() - started_at,
        )

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