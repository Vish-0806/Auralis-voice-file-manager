"""Filesystem Search Service implementation (Phase 11.2).

Provides filesystem search capabilities by query string, glob pattern, file extension,
regex, size range, modification date, case sensitivity, and hidden file inclusion.
"""

from datetime import datetime, timezone
import fnmatch
import os
import re
import time
from typing import List, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.directory_service import DirectoryService
from brain.os.filesystem.exceptions import FileNotFoundError, PathSafetyError
from brain.os.filesystem.filesystem_models import FilesystemEntry, SearchResult
from brain.os.filesystem.interfaces import (
    IDirectoryService,
    IFilesystemSearchService,
    IMetadataService,
)
from brain.os.filesystem.metadata_service import MetadataService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class FilesystemSearchService(IFilesystemSearchService):
    """Provides search over filesystem directories matching criteria."""

    def __init__(
        self,
        path_service: Optional[IPathService] = None,
        directory_service: Optional[IDirectoryService] = None,
        metadata_service: Optional[IMetadataService] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector
        )
        self._path_service = path_service or PathService(
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._metadata_service = metadata_service or MetadataService(
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._directory_service = directory_service or DirectoryService(
            path_service=self._path_service,
            metadata_service=self._metadata_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )

    def _resolve_and_validate(self, path: str) -> str:
        if not path:
            raise FileNotFoundError("Path cannot be empty", path=path)

        abs_path = self._path_service.resolve_absolute(path)
        if not self._path_service.is_safe_path(abs_path):
            raise PathSafetyError("Directory traversal detected", path=path)

        return abs_path

    def search(
        self,
        root_path: str,
        query: str = "",
        pattern: Optional[str] = None,
        extension: Optional[str] = None,
        regex: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None,
        recursive: bool = True,
        case_sensitive: bool = False,
        include_hidden: bool = False,
    ) -> SearchResult:
        """Perform search across filesystem tree matching criteria."""
        start_t = time.time()
        abs_root = self._resolve_and_validate(root_path)

        if not os.path.exists(abs_root) or not os.path.isdir(abs_root):
            raise FileNotFoundError(f"Root search directory not found: {abs_root}", path=root_path)

        matches: List[FilesystemEntry] = []
        errors: List[str] = []

        compiled_regex: Optional[re.Pattern] = None
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_regex = re.compile(regex, flags)
            except Exception as e:
                errors.append(f"Invalid regex '{regex}': {e}")

        # Normalize target extension
        norm_ext = extension.lower() if extension and not case_sensitive else extension
        if norm_ext and not norm_ext.startswith("."):
            norm_ext = f".{norm_ext}"

        query_str = query if case_sensitive else query.lower()

        try:
            candidates = self._directory_service.traverse_directory(
                abs_root, recursive=recursive
            )
        except Exception as e:
            errors.append(f"Traversal error: {e}")
            candidates = []

        for entry in candidates:
            if not include_hidden and entry.is_hidden:
                continue

            entry_name = entry.name if case_sensitive else entry.name.lower()

            # Query substring check
            if query_str and query_str not in entry_name:
                continue

            # Glob pattern check
            if pattern:
                pat = pattern if case_sensitive else pattern.lower()
                if not fnmatch.fnmatch(entry_name, pat):
                    continue

            # Extension check
            if norm_ext:
                entry_ext = entry.extension if case_sensitive else entry.extension.lower()
                if entry_ext != norm_ext:
                    continue

            # Regex check
            if compiled_regex and not compiled_regex.search(entry.name):
                continue

            # Size check
            if min_size is not None and entry.size_bytes < min_size:
                continue
            if max_size is not None and entry.size_bytes > max_size:
                continue

            # Date checks
            if modified_after and entry.modified_at and entry.modified_at < modified_after:
                continue
            if modified_before and entry.modified_at and entry.modified_at > modified_before:
                continue

            matches.append(entry)

        duration = (time.time() - start_t) * 1000.0
        return SearchResult(
            query=query,
            total_matches=len(matches),
            matches=matches,
            search_duration_ms=duration,
            errors=errors,
        )
