"""Search Engine for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe, paginated filesystem search with wildcard, regex,
extension, size, and date filtering.
"""

import fnmatch
import logging
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from brain.filesystem.filesystem_models import (
    SearchMatch,
    SearchResult,
    SortField,
    SortOrder,
)

logger = logging.getLogger(__name__)


class SearchEngine:
    """Thread-safe filesystem search with filtering, sorting, and pagination.

    Supports:
    - Wildcard search (``fnmatch``)
    - Regex search (``re``)
    - Extension filtering
    - Size range filtering
    - Modification date range filtering
    - Recursive / non-recursive traversal
    - Ascending / descending sorting by name, size, modified, extension
    - Pagination
    """

    def __init__(self) -> None:
        """Initializes SearchEngine."""
        self._lock = threading.RLock()
        logger.debug("SearchEngine initialized")

    def search(
        self,
        root: str,
        pattern: str = "*",
        recursive: bool = True,
        use_regex: bool = False,
        extensions: Optional[List[str]] = None,
        min_size_bytes: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None,
        include_directories: bool = False,
        sort_by: SortField = SortField.NAME,
        sort_order: SortOrder = SortOrder.ASCENDING,
        page: int = 1,
        page_size: int = 100,
    ) -> SearchResult:
        """Execute a filesystem search query.

        Args:
            root: Root directory to search from.
            pattern: Wildcard or regex pattern to match filenames against.
            recursive: If True, traverse subdirectories.
            use_regex: If True, treat *pattern* as a regular expression.
            extensions: Optional list of file extensions to include (e.g. ``['.txt', '.py']``).
            min_size_bytes: Exclude files smaller than this.
            max_size_bytes: Exclude files larger than this.
            modified_after: Exclude files modified before this datetime.
            modified_before: Exclude files modified after this datetime.
            include_directories: If True, include directories in results.
            sort_by: Field to sort results by.
            sort_order: Ascending or descending.
            page: 1-based page number.
            page_size: Number of results per page.

        Returns:
            Immutable :class:`SearchResult`.
        """
        with self._lock:
            t0 = time.monotonic()
            logger.info("Operation Started: SEARCH root=%s pattern=%s", root, pattern)

            try:
                root_path = Path(root)
                if not root_path.exists() or not root_path.is_dir():
                    return SearchResult(
                        query=pattern,
                        root_path=root,
                        metadata={"error": f"Root directory not found: {root}"},
                    )

                # Compile regex if needed
                compiled_regex: Optional[re.Pattern] = None
                if use_regex:
                    try:
                        compiled_regex = re.compile(pattern, re.IGNORECASE)
                    except re.error as exc:
                        return SearchResult(
                            query=pattern,
                            root_path=root,
                            metadata={"error": f"Invalid regex: {exc}"},
                        )

                # Normalize extension list
                normalized_exts: Optional[List[str]] = None
                if extensions:
                    normalized_exts = [
                        ext if ext.startswith(".") else f".{ext}"
                        for ext in extensions
                    ]

                # Traverse
                iterator = root_path.rglob("*") if recursive else root_path.iterdir()
                matches: List[SearchMatch] = []

                for entry in iterator:
                    # Skip directories unless requested
                    if entry.is_dir() and not include_directories:
                        continue

                    # Pattern match
                    if not self._matches_pattern(entry.name, pattern, compiled_regex, use_regex):
                        continue

                    # Extension filter
                    if normalized_exts and entry.suffix.lower() not in [e.lower() for e in normalized_exts]:
                        continue

                    # Size filter
                    try:
                        entry_stat = entry.stat()
                    except (OSError, PermissionError):
                        continue

                    size = entry_stat.st_size if entry.is_file() else 0
                    if min_size_bytes is not None and size < min_size_bytes:
                        continue
                    if max_size_bytes is not None and size > max_size_bytes:
                        continue

                    # Date filter
                    modified_at = datetime.fromtimestamp(entry_stat.st_mtime, tz=timezone.utc)
                    if modified_after and modified_at < modified_after:
                        continue
                    if modified_before and modified_at > modified_before:
                        continue

                    matches.append(
                        SearchMatch(
                            path=str(entry),
                            name=entry.name,
                            extension=entry.suffix,
                            size_bytes=size,
                            modified_at=modified_at,
                            is_directory=entry.is_dir(),
                        )
                    )

                # Sort
                matches = _sort_matches(matches, sort_by, sort_order)

                total = len(matches)
                # Paginate (1-based)
                page = max(1, page)
                page_size = max(1, page_size)
                start = (page - 1) * page_size
                end = start + page_size
                page_matches = matches[start:end]
                total_pages = max(1, (total + page_size - 1) // page_size)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: SEARCH matches=%d duration_ms=%.1f", total, duration)

                return SearchResult(
                    query=pattern,
                    root_path=root,
                    matches=page_matches,
                    total_matches=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    duration_ms=duration,
                )

            except Exception as exc:
                logger.error("Operation Failed: SEARCH root=%s error=%s", root, exc)
                duration = (time.monotonic() - t0) * 1000
                return SearchResult(
                    query=pattern,
                    root_path=root,
                    duration_ms=duration,
                    metadata={"error": str(exc)},
                )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _matches_pattern(
        self,
        name: str,
        pattern: str,
        compiled_regex: Optional[re.Pattern],
        use_regex: bool,
    ) -> bool:
        """Return True if *name* matches the search pattern."""
        if use_regex and compiled_regex is not None:
            return bool(compiled_regex.search(name))
        return fnmatch.fnmatch(name.lower(), pattern.lower())


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _sort_key(match: SearchMatch, field: SortField):
    """Return the sort key value for a SearchMatch."""
    if field == SortField.NAME:
        return match.name.lower()
    if field == SortField.SIZE:
        return match.size_bytes
    if field == SortField.MODIFIED:
        return match.modified_at or datetime.min.replace(tzinfo=timezone.utc)
    if field == SortField.EXTENSION:
        return match.extension.lower()
    return match.name.lower()


def _sort_matches(
    matches: List[SearchMatch],
    sort_by: SortField,
    sort_order: SortOrder,
) -> List[SearchMatch]:
    """Sort *matches* in place and return the list."""
    reverse = sort_order == SortOrder.DESCENDING
    return sorted(matches, key=lambda m: _sort_key(m, sort_by), reverse=reverse)
