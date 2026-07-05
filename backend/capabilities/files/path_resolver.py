"""Path resolution helpers for the file capability.

This module resolves a small set of supported Windows user folders into
absolute filesystem paths. The resolver intentionally stays narrow so the file
capability can safely open only known, user-facing locations.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path


class PathResolver:
    """Resolves supported folder names into absolute system paths."""

    _SUPPORTED_FOLDERS: dict[str, str] = {
        "desktop": "Desktop",
        "downloads": "Downloads",
        "documents": "Documents",
    }

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the resolver.

        Args:
            logger: Optional logger used for resolution diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def resolve(self, folder_name: str | None) -> str | None:
        """Resolves a supported folder name to an absolute path.

        Args:
            folder_name: The folder name or alias to resolve.

        Returns:
            The absolute system path for the folder, or ``None`` if unresolved.
        """

        normalized_folder = self._normalize_folder_name(folder_name)
        if normalized_folder is None:
            self._logger.debug("Unsupported folder name received", extra={"folder_name": folder_name})
            return None

        base_path = Path.home()
        resolved_path = base_path / self._SUPPORTED_FOLDERS[normalized_folder]
        if not resolved_path.exists():
            self._logger.debug(
                "Resolved folder does not exist",
                extra={"folder_name": folder_name, "path": str(resolved_path)},
            )
            return None

        return str(resolved_path.resolve())

    def _normalize_folder_name(self, folder_name: str | None) -> str | None:
        """Normalizes a folder name to one of the supported identifiers."""

        if not isinstance(folder_name, str):
            return None

        normalized = folder_name.strip().lower()
        if not normalized:
            return None

        for canonical_name in self._SUPPORTED_FOLDERS:
            if re.search(rf"\b{re.escape(canonical_name)}\b", normalized):
                return canonical_name

        return None


__all__ = ["PathResolver"]