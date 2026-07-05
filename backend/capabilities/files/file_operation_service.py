"""File rename and delete helpers for the file capability.

This module encapsulates safe rename and delete operations so the file
capability can remain focused on request orchestration and validation. Delete
operations prefer moving items to the recycle bin via ``send2trash``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from send2trash import send2trash


class FileOperationService:
    """Performs safe rename and delete operations for files and folders."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the operation service.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def rename(self, source_path: str, new_name: str) -> dict[str, Any]:
        """Renames a file or folder within its current parent directory.

        Args:
            source_path: Absolute path to the source file or folder.
            new_name: The new file or folder name.

        Returns:
            A structured result describing the outcome.
        """

        source = self._normalize_path(source_path)
        normalized_name = self._normalize_name(new_name)

        if source is None or normalized_name is None:
            return self._error_result(
                operation="rename",
                message="Source path and new name must be valid non-empty values.",
                error_class="ValueError",
            )

        if not source.exists():
            return self._error_result(
                operation="rename",
                message=f"Source path '{source}' does not exist.",
                error_class="FileNotFoundError",
            )

        if not self._is_valid_name(normalized_name):
            return self._error_result(
                operation="rename",
                message=f"New name '{normalized_name}' is not valid.",
                error_class="ValueError",
            )

        destination = source.with_name(normalized_name)
        if destination.exists():
            return self._error_result(
                operation="rename",
                message=f"Destination path '{destination}' already exists.",
                error_class="FileExistsError",
            )

        try:
            self._logger.info(
                "Renaming item",
                extra={"source": str(source), "destination": str(destination)},
            )
            source.rename(destination)
            return {
                "status": "success",
                "message": f"Successfully renamed '{source.name}' to '{destination.name}'.",
                "source": str(source),
                "destination": str(destination),
                "operation": "rename",
            }
        except PermissionError as exc:
            self._logger.exception(
                "Permission error renaming item",
                extra={"source": str(source), "destination": str(destination)},
            )
            return self._error_result(
                operation="rename",
                message=f"Permission denied while renaming '{source.name}'.",
                error_class="PermissionError",
                error=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "Unexpected error renaming item",
                extra={"source": str(source), "destination": str(destination)},
            )
            return self._error_result(
                operation="rename",
                message=f"An error occurred while renaming '{source.name}'.",
                error_class=exc.__class__.__name__,
                error=str(exc),
            )

    def delete(self, target_path: str) -> dict[str, Any]:
        """Moves a file or folder to the recycle bin.

        Args:
            target_path: Absolute path to the file or folder to delete.

        Returns:
            A structured result describing the outcome.
        """

        target = self._normalize_path(target_path)
        if target is None:
            return self._error_result(
                operation="delete",
                message="Target path must be a valid non-empty value.",
                error_class="ValueError",
            )

        if not target.exists():
            return self._error_result(
                operation="delete",
                message=f"Target path '{target}' does not exist.",
                error_class="FileNotFoundError",
            )

        try:
            self._logger.info("Sending item to recycle bin", extra={"target": str(target)})
            send2trash(str(target))
            return {
                "status": "success",
                "message": f"Successfully deleted '{target.name}' to the Recycle Bin.",
                "target": str(target),
                "operation": "delete",
            }
        except PermissionError as exc:
            self._logger.exception("Permission error deleting item", extra={"target": str(target)})
            return self._error_result(
                operation="delete",
                message=f"Permission denied while deleting '{target.name}'.",
                error_class="PermissionError",
                error=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception("Unexpected error deleting item", extra={"target": str(target)})
            return self._error_result(
                operation="delete",
                message=f"An error occurred while deleting '{target.name}'.",
                error_class=exc.__class__.__name__,
                error=str(exc),
            )

    def _normalize_path(self, path_value: str) -> Path | None:
        """Normalizes a string path into a Path object."""

        if not isinstance(path_value, str):
            return None

        cleaned = path_value.strip()
        if not cleaned:
            return None

        return Path(cleaned).expanduser()

    def _normalize_name(self, name_value: str) -> str | None:
        """Normalizes a new file or folder name."""

        if not isinstance(name_value, str):
            return None

        cleaned = name_value.strip()
        return cleaned if cleaned else None

    def _is_valid_name(self, name_value: str) -> bool:
        """Checks whether a proposed name is safe to use on disk."""

        invalid_chars = {"/", "\\", ":", "*", "?", '"', "<", ">", "|"}
        return bool(name_value) and not any(char in name_value for char in invalid_chars) and name_value not in {".", ".."}

    def _error_result(
        self,
        operation: str,
        message: str,
        error_class: str,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Builds a structured error payload for file operations."""

        return {
            "status": "error",
            "message": message,
            "error_class": error_class,
            "error": error,
            "operation": operation,
        }


__all__ = ["FileOperationService"]