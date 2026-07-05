"""Folder operations service for Auralis.

This module encapsulates creation, checking existence, validating name, and safe
deletion of folders, preferring moving them to the Recycle Bin using send2trash.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from send2trash import send2trash


class FolderService:
    """Performs safe folder operations such as creation and deletion."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the FolderService.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def validate_folder_name(self, folder_name: str) -> bool:
        """Checks whether a folder name is syntactically valid and safe.

        Args:
            folder_name: The proposed folder name.

        Returns:
            True if the name is valid, otherwise False.
        """

        if not isinstance(folder_name, str):
            return False

        cleaned = folder_name.strip()
        if not cleaned:
            return False

        # Windows invalid characters for folder/filenames
        invalid_chars = {"/", "\\", ":", "*", "?", '"', "<", ">", "|"}
        if any(char in cleaned for char in invalid_chars):
            return False

        # Forbidden names
        if cleaned in {".", ".."}:
            return False

        return True

    def folder_exists(self, folder_path: str) -> bool:
        """Checks if a directory exists at the given path.

        Args:
            folder_path: Absolute or relative path to check.

        Returns:
            True if the directory exists, otherwise False.
        """

        path = Path(folder_path).expanduser()
        return path.exists() and path.is_dir()

    def create_folder(self, folder_name: str, parent_path: str) -> dict[str, Any]:
        """Creates a new folder safely under the given parent folder.

        Args:
            folder_name: Name of the folder to create.
            parent_path: Path of the parent directory.

        Returns:
            A dictionary containing status, message, and path if successful.
        """

        if not self.validate_folder_name(folder_name):
            return {
                "status": "error",
                "message": f"Folder name '{folder_name}' is invalid.",
                "error_class": "ValueError",
                "operation": "create_folder",
            }

        parent = Path(parent_path).expanduser().resolve()
        if not parent.exists() or not parent.is_dir():
            return {
                "status": "error",
                "message": f"Parent path '{parent_path}' does not exist or is not a directory.",
                "error_class": "FileNotFoundError",
                "operation": "create_folder",
            }

        target_path = parent / folder_name.strip()

        if target_path.exists():
            return {
                "status": "error",
                "message": f"Folder '{folder_name}' already exists at '{parent_path}'.",
                "error_class": "FileExistsError",
                "operation": "create_folder",
            }

        try:
            self._logger.info(
                "Creating folder",
                extra={"folder_name": folder_name, "parent_path": str(parent), "target_path": str(target_path)},
            )
            target_path.mkdir(parents=True, exist_ok=False)
            return {
                "status": "success",
                "message": f"Successfully created folder '{folder_name}' at '{target_path.parent}'.",
                "path": str(target_path),
                "operation": "create_folder",
            }
        except PermissionError as exc:
            self._logger.exception(
                "Permission error creating folder",
                extra={"target_path": str(target_path)},
            )
            return {
                "status": "error",
                "message": f"Permission denied while creating folder '{folder_name}'.",
                "error_class": "PermissionError",
                "error": str(exc),
                "operation": "create_folder",
            }
        except Exception as exc:
            self._logger.exception(
                "Unexpected error creating folder",
                extra={"target_path": str(target_path)},
            )
            return {
                "status": "error",
                "message": f"An error occurred while creating folder '{folder_name}'.",
                "error_class": exc.__class__.__name__,
                "error": str(exc),
                "operation": "create_folder",
            }

    def delete_folder(self, folder_path: str) -> dict[str, Any]:
        """Safely moves a folder to the Recycle Bin.

        Args:
            folder_path: Absolute path to the folder.

        Returns:
            A dictionary containing status, message, and target if successful.
        """

        path = Path(folder_path).expanduser().resolve()

        if not path.exists():
            return {
                "status": "error",
                "message": f"Folder '{folder_path}' does not exist.",
                "error_class": "FileNotFoundError",
                "operation": "delete_folder",
            }

        if not path.is_dir():
            return {
                "status": "error",
                "message": f"Path '{folder_path}' is not a directory.",
                "error_class": "ValueError",
                "operation": "delete_folder",
            }

        if self.is_protected_folder(path):
            return {
                "status": "error",
                "message": f"Folder '{path.name}' is a protected system folder and cannot be deleted.",
                "error_class": "PermissionError",
                "operation": "delete_folder",
            }

        try:
            self._logger.info("Moving folder to recycle bin", extra={"target": str(path)})
            send2trash(str(path))
            return {
                "status": "success",
                "message": f"Successfully deleted '{path.name}' to the Recycle Bin.",
                "target": str(path),
                "operation": "delete_folder",
            }
        except PermissionError as exc:
            self._logger.exception("Permission error deleting folder", extra={"target": str(path)})
            return {
                "status": "error",
                "message": f"Permission denied while deleting folder '{path.name}'.",
                "error_class": "PermissionError",
                "error": str(exc),
                "operation": "delete_folder",
            }
        except Exception as exc:
            self._logger.exception("Unexpected error deleting folder", extra={"target": str(path)})
            return {
                "status": "error",
                "message": f"An error occurred while deleting folder '{path.name}'.",
                "error_class": exc.__class__.__name__,
                "error": str(exc),
                "operation": "delete_folder",
            }

    def is_protected_folder(self, path: Path) -> bool:
        """Determines if a directory path points to a protected system folder.

        Args:
            path: Absolute path to evaluate.

        Returns:
            True if the folder is protected, otherwise False.
        """

        abs_path = path.resolve()

        # Check drive roots
        if abs_path == abs_path.parent:
            return True

        # System paths
        protected_paths = {
            Path(os.environ.get("SystemRoot", "C:\\Windows")).resolve(),
            Path(os.environ.get("windir", "C:\\Windows")).resolve(),
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")).resolve(),
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")).resolve(),
            Path(os.environ.get("ProgramData", "C:\\ProgramData")).resolve(),
            Path(os.environ.get("USERPROFILE", Path.home())).resolve(),
        }

        # Add home standard directories
        home = Path.home().resolve()
        for std_dir in ["Desktop", "Downloads", "Documents", "Pictures", "Music", "Videos"]:
            protected_paths.add((home / std_dir).resolve())

        if abs_path in protected_paths:
            return True

        # Check if target path is a parent of any critical folder to prevent recursive deletes
        for p in protected_paths:
            if abs_path in p.parents:
                return True

        return False
