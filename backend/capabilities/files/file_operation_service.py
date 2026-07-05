"""File rename and delete helpers for the file capability.

This module encapsulates safe rename and delete operations so the file
capability can remain focused on request orchestration and validation. Delete
operations prefer moving items to the recycle bin via ``send2trash``.
"""

from __future__ import annotations

import logging
import os
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

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Retrieves detailed information and metadata for a file or folder.

        Args:
            file_path: Absolute path to the file or folder.

        Returns:
            A dictionary containing status, metadata fields, and formatted report if successful.
        """

        target = self._normalize_path(file_path)
        if target is None:
            return self._error_result(
                operation="get_file_info",
                message="File path must be a valid non-empty value.",
                error_class="ValueError",
            )

        if not target.exists():
            return self._error_result(
                operation="get_file_info",
                message=f"File path '{target}' does not exist.",
                error_class="FileNotFoundError",
            )

        try:
            st = target.stat()
            from datetime import datetime

            raw_size = st.st_size
            if raw_size < 1024:
                size_str = f"{raw_size} bytes"
            elif raw_size < 1024 * 1024:
                size_str = f"{raw_size / 1024:.1f} KB ({raw_size:,} bytes)"
            else:
                size_str = f"{raw_size / (1024 * 1024):.1f} MB ({raw_size:,} bytes)"

            if target.is_dir():
                type_desc = "Directory"
                ext = ""
            else:
                ext = target.suffix
                type_map = {
                    ".pdf": "PDF Document",
                    ".txt": "Text Document",
                    ".md": "Markdown Document",
                    ".py": "Python Script",
                    ".exe": "Executable Application",
                    ".zip": "ZIP Archive",
                    ".rar": "RAR Archive",
                    ".7z": "7-Zip Archive",
                    ".xlsx": "Excel Spreadsheet",
                    ".xls": "Excel Spreadsheet",
                    ".csv": "CSV Spreadsheet",
                    ".pptx": "PowerPoint Presentation",
                    ".docx": "Word Document",
                    ".png": "PNG Image",
                    ".jpg": "JPEG Image",
                    ".jpeg": "JPEG Image",
                    ".gif": "GIF Image",
                    ".mp4": "MP4 Video",
                    ".mp3": "MP3 Audio",
                }
                type_desc = type_map.get(ext.lower(), f"{ext.upper()[1:]} File" if ext else "File")

            created_date = datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            modified_date = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            mode = st.st_mode
            perms = []
            if os.access(target, os.R_OK):
                perms.append("Read")
            if os.access(target, os.W_OK):
                perms.append("Write")
            if os.access(target, os.X_OK):
                perms.append("Execute")
            perms_str = ", ".join(perms) if perms else "None"

            hidden = self._is_hidden_file(target)

            info = {
                "name": target.name,
                "extension": ext,
                "type": type_desc,
                "size": size_str,
                "created_date": created_date,
                "modified_date": modified_date,
                "absolute_path": str(target.resolve()),
                "permissions": perms_str,
                "hidden_status": str(hidden),
            }

            report_lines = [
                f"File Information for {target.name}:",
                f"- File Name: {target.name}",
                f"- Extension: {ext if ext else 'None'}",
                f"- Type: {type_desc}",
                f"- Size: {size_str}",
                f"- Created Date: {created_date}",
                f"- Modified Date: {modified_date}",
                f"- Absolute Path: {info['absolute_path']}",
                f"- Permissions: {perms_str}",
                f"- Hidden Status: {info['hidden_status']}",
            ]
            report = "\n".join(report_lines)

            return {
                "status": "success",
                "message": report,
                "info": info,
                "operation": "get_file_info",
            }
        except PermissionError as exc:
            self._logger.exception("Permission error reading file info", extra={"target": str(target)})
            return self._error_result(
                operation="get_file_info",
                message=f"Permission denied while reading information for '{target.name}'.",
                error_class="PermissionError",
                error=str(exc),
            )
        except Exception as exc:
            self._logger.exception("Unexpected error reading file info", extra={"target": str(target)})
            return self._error_result(
                operation="get_file_info",
                message=f"An error occurred while reading information for '{target.name}'.",
                error_class=exc.__class__.__name__,
                error=str(exc),
            )

    def _is_hidden_file(self, path: Path) -> bool:
        """Checks if a file is hidden."""

        if path.name.startswith("."):
            return True
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:
                return bool(attrs & 2)
        except Exception:
            pass
        return False


__all__ = ["FileOperationService"]