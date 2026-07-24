"""Workspace Intelligence Coordinator for coordinating indexers, detectors, and caching results."""

import os
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from memory.workspace.workspace_indexer import WorkspaceIndexer
from memory.workspace.project_intelligence import ProjectIntelligenceEngine
from memory.workspace.workspace_analysis import WorkspaceAnalysis

logger = logging.getLogger(__name__)


class WorkspaceCache:
    """Thread-safe in-memory cache for storing WorkspaceAnalysis records with a TTL."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        """Initializes the WorkspaceCache.

        Args:
            ttl_seconds: Cache TTL in seconds (default is 5 minutes).
        """
        self.ttl = ttl_seconds
        self._cache: Dict[str, Tuple[WorkspaceAnalysis, float]] = {}
        self._lock = threading.Lock()

    def get(self, path: str) -> Optional[WorkspaceAnalysis]:
        """Retrieves a cached analysis if it exists and has not expired.

        Args:
            path: Normalized workspace path.

        Returns:
            The WorkspaceAnalysis instance, or None if expired/not found.
        """
        with self._lock:
            cached = self._cache.get(path)
            if not cached:
                return None

            analysis, cache_time = cached
            if time.time() - cache_time > self.ttl:
                # Cache expired, purge it
                if path in self._cache:
                    del self._cache[path]
                return None
            return analysis

    def set(self, path: str, analysis: WorkspaceAnalysis) -> None:
        """Stores an analysis result in cache.

        Args:
            path: Normalized workspace path.
            analysis: The WorkspaceAnalysis record to cache.
        """
        with self._lock:
            self._cache[path] = (analysis, time.time())

    def invalidate(self, path: str) -> None:
        """Purges a single path cache entry.

        Args:
            path: Normalized workspace path.
        """
        with self._lock:
            if path in self._cache:
                del self._cache[path]

    def clear(self) -> None:
        """Purges all entries from the cache."""
        with self._lock:
            self._cache.clear()


class WorkspaceIntelligenceCoordinator:
    """Coordinates filesystem crawling and project analysis steps, utilizing caching."""

    def __init__(
        self,
        indexer: Optional[WorkspaceIndexer] = None,
        engine: Optional[ProjectIntelligenceEngine] = None,
        cache_ttl: float = 300.0,
    ) -> None:
        """Initializes the WorkspaceIntelligenceCoordinator.

        Args:
            indexer: Optional custom WorkspaceIndexer instance.
            engine: Optional custom ProjectIntelligenceEngine instance.
            cache_ttl: Cache TTL in seconds (default is 5 minutes).
        """
        self.indexer = indexer or WorkspaceIndexer()
        self.engine = engine or ProjectIntelligenceEngine()
        self.cache = WorkspaceCache(ttl_seconds=cache_ttl)

    def _normalize_path(self, path: str) -> str:
        """Helper to resolve absolute physical directory path strings."""
        return os.path.abspath(path)

    async def analyze(self, workspace_path: str, force_refresh: bool = False) -> WorkspaceAnalysis:
        """Enforces workflow indexing and project parsing, returning analysis results.

        Checks and populates WorkspaceCache if valid.

        Args:
            workspace_path: Target root directory path.
            force_refresh: If True, bypasses cache and initiates a full scan.

        Returns:
            The compiled WorkspaceAnalysis domain model.
        """
        norm_path = self._normalize_path(workspace_path)

        if not force_refresh:
            cached_result = self.cache.get(norm_path)
            if cached_result:
                logger.info(f"Cache hit for workspace: {norm_path}")
                return cached_result

        logger.info(f"Cache miss or force refresh. Analyzing workspace: {norm_path}")

        # Invoke WorkspaceIndexer
        index = await self.indexer.index(norm_path, force_refresh=force_refresh)

        # Pass index into ProjectIntelligenceEngine
        analysis = await self.engine.analyze(index)

        # Cache results
        self.cache.set(norm_path, analysis)

        return analysis

    async def refresh(self, workspace_path: str) -> WorkspaceAnalysis:
        """Triggers a force-refreshed scan and updates the cache.

        Args:
            workspace_path: Target root directory path.

        Returns:
            The newly compiled WorkspaceAnalysis domain model.
        """
        return await self.analyze(workspace_path, force_refresh=True)

    def invalidate(self, workspace_path: str) -> None:
        """Clears a single path entry from the workspace cache.

        Args:
            workspace_path: Target root directory path.
        """
        norm_path = self._normalize_path(workspace_path)
        self.cache.invalidate(norm_path)

    def clear_cache(self) -> None:
        """Purges all entries from the workspace cache."""
        self.cache.clear()
