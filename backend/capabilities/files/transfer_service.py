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

    def _get_unique_destination(self, source: Path, destination: Path) -> Path:
        """Determines a unique destination path to avoid collisions."""
        basename = source.name
        if source.is_file():
            name, ext = source.stem, source.suffix
        else:
            name, ext = basename, ""

        dest_path = destination / basename
        counter = 1
        while dest_path.exists():
            if ext:
                new_name = f"{name}_{counter}{ext}"
            else:
                new_name = f"{name}_{counter}"
            dest_path = destination / new_name
            counter += 1
        return dest_path

    def _transfer(self, source_path: str, destination_path: str, operation: str) -> dict[str, Any]:
        """Validates and performs a safe copy or move transfer."""

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
                message=f"Source path '{source}' does not exist.",
                error_class="FileNotFoundError",
            )

        # Create destination directory if it does not exist (migrated from legacy)
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return self._error_result(
                operation=operation,
                message=f"Failed to create destination folder '{destination}': {exc}",
                error_class="PermissionError",
                error=str(exc),
            )

        if not destination.is_dir():
            return self._error_result(
                operation=operation,
                message=f"Destination path '{destination}' is not a folder.",
                error_class="NotADirectoryError",
            )

        target_path = self._get_unique_destination(source, destination)

        try:
            self._logger.info(
                "Transferring item",
                extra={"operation": operation, "source": str(source), "destination": str(target_path)},
            )
            if operation == "copy":
                if source.is_dir():
                    shutil.copytree(str(source), str(target_path))
                else:
                    shutil.copy2(str(source), str(target_path))
            else:
                shutil.move(str(source), str(target_path))

            return {
                "status": "success",
                "message": f"Successfully {self._PAST_TENSE[operation]} '{source.name}' to '{destination.name}'.",
                "source": str(source),
                "destination": str(target_path),
                "operation": operation,
            }
        except PermissionError as exc:
            self._logger.exception(
                "Permission error during transfer",
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
                "Unexpected error during transfer",
                extra={"operation": operation, "source": str(source), "destination": str(target_path)},
            )
            return self._error_result(
                operation=operation,
                message=f"An error occurred while attempting to {operation} '{source.name}': {exc}",
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