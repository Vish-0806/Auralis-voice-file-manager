"""Source path resolution for files and folders."""

from __future__ import annotations

import logging
import os
from typing import Any
from pathlib import Path
from .search_engine import SearchEngine
from .path_resolver import PathResolver


class SourceResolver:
    """Resolves target names or paths to absolute paths with disambiguation support."""

    def __init__(self, logger: logging.Logger | None = None, search_engine: SearchEngine | None = None, search_fn = None) -> None:
        """Initializes the source resolver.

        Args:
            logger: Optional logger for diagnostics.
            search_engine: Optional search engine.
            search_fn: Optional legacy search function.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._search_engine = search_engine or SearchEngine(logger=self._logger)
        self._search_fn = search_fn

    def resolve(self, target: str) -> dict[str, Any]:
        """Resolves target name/path to a unique path.

        Args:
            target: The file/folder name or path.

        Returns:
            A dictionary containing status, path or results, and message.
        """

        if not target:
            return {
                "status": "error",
                "message": "Target name is empty.",
                "error_class": "ValueError",
            }

        # If target is already a valid path on disk, use it directly
        if os.path.exists(target):
            self._logger.info("Target '%s' resolved directly (exists on disk).", target)
            return {
                "status": "success",
                "path": os.path.abspath(target),
                "message": "Target exists on disk.",
            }

        if self._search_fn is not None:
            results = self._search_fn(target)
        else:
            self._logger.info("Searching for target: '%s' using search engine.", target)
            matching_paths = self._search_engine.search(target)

            # Legacy search returned dictionaries: [{'name': ..., 'path': ..., 'type': ...}]
            # Let's map matching paths to this format to match source resolver expectations
            results = []
            for path_str in matching_paths:
                basename = os.path.basename(path_str)
                _, ext = os.path.splitext(basename)
                results.append({
                    "name": basename,
                    "path": path_str,
                    "type": ext
                })

        if not results:
            self._logger.warning("No files found matching target: '%s'", target)
            return {
                "status": "error",
                "message": f"File '{target}' not found.",
                "error_class": "FileNotFoundError",
            }

        if len(results) == 1:
            resolved_path = results[0]["path"]
            self._logger.info("Target '%s' resolved to unique path: '%s'", target, resolved_path)
            return {
                "status": "success",
                "path": resolved_path,
                "message": "Found exactly one matching file.",
            }

        # Multiple files found
        self._logger.info("Multiple matches found for target '%s': %d matches.", target, len(results))
        return {
            "status": "disambiguation",
            "message": f"Multiple files found matching '{target}'.",
            "results": results,
        }
