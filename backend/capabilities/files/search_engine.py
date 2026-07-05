"""Recursive file search for the file capability.

This module searches the supported user folders for matching files and folders
using a narrow, deterministic rule set. The engine is intentionally local and
filesystem-only so it can be used safely by the assistant pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .path_resolver import PathResolver


class SearchEngine:
    """Searches Desktop, Downloads, and Documents recursively."""

    _SUPPORTED_SCOPE_FOLDERS: tuple[str, ...] = ("Desktop", "Downloads", "Documents")

    def __init__(self, logger: logging.Logger | None = None, path_resolver: PathResolver | None = None) -> None:
        """Initializes the search engine.

        Args:
            logger: Optional logger for diagnostics.
            path_resolver: Optional resolver used to locate supported roots.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._path_resolver = path_resolver or PathResolver(logger=self._logger)

    def search(self, query: str | None) -> list[str]:
        """Searches recursively for files and folders matching the query.

        Args:
            query: The search term.

        Returns:
            A list of absolute matching paths.
        """

        normalized_query = self._normalize_query(query)
        if normalized_query is None:
            self._logger.info("Empty search query received")
            return []

        matches: list[str] = []
        for scope_root in self._resolve_scope_roots():
            if scope_root is None:
                continue

            self._logger.info("Searching scope", extra={"scope_root": str(scope_root), "query": normalized_query})
            matches.extend(self._search_scope(scope_root, normalized_query))

        deduplicated_matches = list(dict.fromkeys(matches))
        self._logger.info(
            "Search completed",
            extra={"query": normalized_query, "match_count": len(deduplicated_matches)},
        )
        return deduplicated_matches

    def _resolve_scope_roots(self) -> list[Path | None]:
        """Resolves the supported search roots.

        Returns:
            A list of resolved root paths or ``None`` entries when unavailable.
        """

        roots: list[Path | None] = []
        for folder_name in self._SUPPORTED_SCOPE_FOLDERS:
            resolved_root = self._path_resolver.resolve(folder_name)
            roots.append(Path(resolved_root) if resolved_root is not None else None)

        return roots

    def _search_scope(self, root: Path, query: str) -> list[str]:
        """Searches a single root recursively for matching files and folders."""

        matches: list[str] = []
        stack: list[Path] = [root]

        while stack:
            current = stack.pop()
            try:
                for entry in current.iterdir():
                    if self._entry_matches(entry, query):
                        matches.append(str(entry.resolve()))

                    if entry.is_dir():
                        stack.append(entry)
            except (PermissionError, OSError) as exc:
                self._logger.warning(
                    "Unable to access directory during search",
                    extra={"path": str(current), "error": str(exc)},
                )

        return matches

    def _entry_matches(self, entry: Path, query: str) -> bool:
        """Checks whether a file-system entry matches the search query."""

        return query in entry.name.lower() or query in str(entry).lower()

    def _normalize_query(self, query: str | None) -> str | None:
        """Normalizes the incoming query string."""

        if not isinstance(query, str):
            return None

        normalized = query.strip().lower()
        if not normalized:
            return None

        return normalized


__all__ = ["SearchEngine"]