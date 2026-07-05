"""File transfer helpers for the file capability.

This module encapsulates copy and move operations so the file capability can
stay focused on orchestration and validation. The service is intentionally
filesystem-only and does not perform any prompting or overwrite behavior.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any


class TransferService:
    """Performs safe copy and move operations for files."""

    _PAST_TENSE: dict[str, str] = {
        "copy": "copied",
        "move": "moved",
    }

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the transfer service.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def copy_file(self, source_path: str, destination_path: str) -> dict[str, Any]:
        """Copies a file into an existing destination folder.

        Args:
            source_path: Absolute path to the source file.
            destination_path: Absolute path to the destination folder.

        Returns:
            A structured result describing the outcome.
        """

        return self._transfer(source_path, destination_path, operation="copy")

    def move_file(self, source_path: str, destination_path: str) -> dict[str, Any]:
        """Moves a file into an existing destination folder.

        Args:
            source_path: Absolute path to the source file.
            destination_path: Absolute path to the destination folder.

        Returns:
            A structured result describing the outcome.
        """

        return self._transfer(source_path, destination_path, operation="move")

    def _transfer(self, source_path: str, destination_path: str, operation: str) -> dict[str, Any]:
        """Validates and performs a safe file transfer."""

        source = self._normalize_path(source_path)
        destination = self._normalize_path(destination_path)

        if source is None or destination is None:
            return self._error_result(
                operation=operation,
                message="Source and destination paths must be valid non-empty strings.",
                error_class="ValueError",
            )

        if not source.exists():
            return self._error_result(
                operation=operation,
                message=f"Source file '{source}' does not exist.",
                error_class="FileNotFoundError",
            )

        if not source.is_file():
            return self._error_result(
                operation=operation,
                message=f"Source path '{source}' is not a file.",
                error_class="IsADirectoryError",
            )

        if not destination.exists():
            return self._error_result(
                operation=operation,
                message=f"Destination folder '{destination}' does not exist.",
                error_class="FileNotFoundError",
            )

        if not destination.is_dir():
            return self._error_result(
                operation=operation,
                message=f"Destination path '{destination}' is not a folder.",
                error_class="NotADirectoryError",
            )

        target_path = destination / source.name
        if target_path.exists():
            return self._error_result(
                operation=operation,
                message=f"Destination file '{target_path}' already exists.",
                error_class="FileExistsError",
            )

        try:
            self._logger.info(
                "Transferring file",
                extra={"operation": operation, "source": str(source), "destination": str(target_path)},
            )
            if operation == "copy":
                shutil.copy2(source, target_path)
            else:
                shutil.move(source, target_path)

            return {
                "status": "success",
                "message": f"Successfully {self._PAST_TENSE[operation]} '{source.name}' to '{destination.name}'.",
                "source": str(source),
                "destination": str(target_path),
                "operation": operation,
            }
        except PermissionError as exc:
            self._logger.exception(
                "Permission error during file transfer",
                extra={"operation": operation, "source": str(source), "destination": str(target_path)},
            )
            return self._error_result(
                operation=operation,
                message=f"Permission denied while attempting to {operation} '{source.name}'.",
                error_class="PermissionError",
                error=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.exception(
                "Unexpected error during file transfer",
                extra={"operation": operation, "source": str(source), "destination": str(target_path)},
            )
            return self._error_result(
                operation=operation,
                message=f"An error occurred while attempting to {operation} '{source.name}'.",
                error_class=exc.__class__.__name__,
                error=str(exc),
            )

    def _normalize_path(self, path_value: str) -> Path | None:
        """Normalizes a string path into a resolved Path object."""

        if not isinstance(path_value, str):
            return None

        cleaned = path_value.strip()
        if not cleaned:
            return None

        return Path(cleaned).expanduser()

    def _error_result(
        self,
        operation: str,
        message: str,
        error_class: str,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Builds a structured error payload for transfer operations."""

        return {
            "status": "error",
            "message": message,
            "error_class": error_class,
            "error": error,
            "operation": operation,
        }


__all__ = ["TransferService"]