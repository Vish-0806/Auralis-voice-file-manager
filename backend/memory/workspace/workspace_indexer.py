"""Workspace Indexing Engine for tracking filesystem metadata and directory statistics."""

import os
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkspaceIndexerConfig(BaseModel):
    """Configuration options for filesystem workspace indexers."""

    ignored_folders: List[str] = Field(
        default_factory=lambda: [".git", "node_modules", "venv", "__pycache__", "build", "dist", "target"],
        description="List of folder names to exclude during indexing."
    )
    ignored_extensions: List[str] = Field(
        default_factory=lambda: [".pyc", ".pyo", ".tmp", ".log", ".obj", ".bin"],
        description="List of file extensions to ignore."
    )
    max_depth: int = Field(default=10, description="Maximum directory nesting depth to crawl.")
    scan_timeout: float = Field(default=30.0, description="Hard timeout in seconds for traversal.")


class WorkspaceFileEntry(BaseModel):
    """Represents a discovered file or directory entry in the index."""

    relative_path: str = Field(description="File path relative to the workspace root.")
    absolute_path: str = Field(description="Full resolved disk path.")
    filename: str = Field(description="Base name of the file or directory.")
    extension: str = Field(description="File extension containing the dot prefix.")
    size: int = Field(description="File size in bytes.")
    modified_time: datetime = Field(description="Timezone-aware file modification timestamp.")
    is_hidden: bool = Field(description="True if the file name begins with a dot.")
    is_directory: bool = Field(description="True if the entry is a directory.")


class WorkspaceIndex(BaseModel):
    """Metadata compilation representing a scanned workspace state."""

    workspace_path: str = Field(description="Root path of the indexed workspace.")
    directories: List[str] = Field(description="List of indexed relative directory paths.")
    files: Dict[str, WorkspaceFileEntry] = Field(description="Mapping of relative paths to entry metadata.")
    directory_count: int = Field(description="Count of indexed directories.")
    file_count: int = Field(description="Count of indexed files.")
    total_size: int = Field(description="Aggregated size in bytes of all indexed files.")
    maximum_depth: int = Field(description="Maximum depth reached during traversal.")
    indexed_at: datetime = Field(description="Timezone-aware indexing timestamp.")


class WorkspaceIndexer:
    """Crawls workspace directory trees and compiles filesystem indexes."""

    def __init__(self, config: Optional[WorkspaceIndexerConfig] = None) -> None:
        """Initializes the WorkspaceIndexer.

        Args:
            config: Optional WorkspaceIndexerConfig instance.
        """
        self.config = config or WorkspaceIndexerConfig()
        self._cache: Dict[str, WorkspaceIndex] = {}

    def _is_hidden(self, path: str, name: str) -> bool:
        """Determines if a directory entry is classified as hidden (starts with a dot)."""
        return name.startswith(".")

    async def index(self, workspace_path: str, force_refresh: bool = False) -> WorkspaceIndex:
        """Indexes the target workspace recursively.

        Args:
            workspace_path: Root folder path to index.
            force_refresh: If True, bypasses cache and performs a full scan.

        Returns:
            A WorkspaceIndex model containing metadata.
        """
        normalized_root = os.path.abspath(workspace_path)
        if not os.path.isdir(normalized_root):
            raise FileNotFoundError(f"Path is not a directory: {normalized_root}")

        cached = self._cache.get(normalized_root)
        if cached and not force_refresh:
            # Perform incremental indexing to optimize performance
            return await self._incremental_index(normalized_root, cached)

        # Execute full filesystem scan
        return await self._full_index(normalized_root)

    async def _full_index(self, root: str) -> WorkspaceIndex:
        """Traverses the filesystem recursively to index root directory contents."""
        start_time = time.time()
        directories: List[str] = []
        files: Dict[str, WorkspaceFileEntry] = {}
        total_size = 0
        max_depth_reached = 0

        def _traverse(path: str, depth: int) -> None:
            nonlocal total_size, max_depth_reached

            if time.time() - start_time > self.config.scan_timeout:
                logger.warning(f"Indexing timed out after {self.config.scan_timeout}s.")
                return

            if depth > self.config.max_depth:
                return

            max_depth_reached = max(max_depth_reached, depth)

            try:
                entries = os.listdir(path)
            except PermissionError:
                return
            except Exception as e:
                logger.error(f"Error reading directory {path}: {e}")
                return

            for entry in entries:
                if entry in self.config.ignored_folders:
                    continue

                full_path = os.path.join(path, entry)
                rel_path = os.path.relpath(full_path, root)
                is_dir = os.path.isdir(full_path)
                is_hidden = self._is_hidden(full_path, entry)

                if is_dir:
                    if os.path.islink(full_path):
                        continue
                    directories.append(rel_path)
                    _traverse(full_path, depth + 1)
                else:
                    _, ext = os.path.splitext(entry)
                    if ext.lower() in self.config.ignored_extensions:
                        continue

                    try:
                        stat = os.stat(full_path)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    except Exception:
                        size = 0
                        mtime = datetime.now(timezone.utc)

                    files[rel_path] = WorkspaceFileEntry(
                        relative_path=rel_path,
                        absolute_path=full_path,
                        filename=entry,
                        extension=ext,
                        size=size,
                        modified_time=mtime,
                        is_hidden=is_hidden,
                        is_directory=False,
                    )
                    total_size += size

        # Offload file system crawl off the asyncio loop thread
        await asyncio.to_thread(_traverse, root, 0)

        index_obj = WorkspaceIndex(
            workspace_path=root,
            directories=directories,
            files=files,
            directory_count=len(directories),
            file_count=len(files),
            total_size=total_size,
            maximum_depth=max_depth_reached,
            indexed_at=datetime.now(timezone.utc),
        )
        self._cache[root] = index_obj
        return index_obj

    async def _incremental_index(self, root: str, cached: WorkspaceIndex) -> WorkspaceIndex:
        """Performs a lightweight incremental scan of disk entries using cached state."""
        start_time = time.time()
        directories: List[str] = []
        files: Dict[str, WorkspaceFileEntry] = {}
        total_size = 0
        max_depth_reached = 0

        def _traverse_incremental(path: str, depth: int) -> None:
            nonlocal total_size, max_depth_reached

            if time.time() - start_time > self.config.scan_timeout:
                logger.warning(f"Incremental indexing timed out after {self.config.scan_timeout}s.")
                return

            if depth > self.config.max_depth:
                return

            max_depth_reached = max(max_depth_reached, depth)

            try:
                entries = os.listdir(path)
            except PermissionError:
                return
            except Exception as e:
                logger.error(f"Error reading directory {path}: {e}")
                return

            for entry in entries:
                if entry in self.config.ignored_folders:
                    continue

                full_path = os.path.join(path, entry)
                rel_path = os.path.relpath(full_path, root)
                is_dir = os.path.isdir(full_path)
                is_hidden = self._is_hidden(full_path, entry)

                if is_dir:
                    if os.path.islink(full_path):
                        continue
                    directories.append(rel_path)
                    _traverse_incremental(full_path, depth + 1)
                else:
                    _, ext = os.path.splitext(entry)
                    if ext.lower() in self.config.ignored_extensions:
                        continue

                    cached_file = cached.files.get(rel_path)
                    try:
                        stat = os.stat(full_path)
                        mtime_float = stat.st_mtime
                        size = stat.st_size
                    except Exception:
                        size = 0
                        mtime_float = 0.0

                    # Verify if cached entry is still valid to prevent object reallocation
                    if (
                        cached_file
                        and abs(cached_file.modified_time.timestamp() - mtime_float) < 1.0
                        and cached_file.size == size
                    ):
                        files[rel_path] = cached_file
                        total_size += cached_file.size
                    else:
                        mtime = (
                            datetime.fromtimestamp(mtime_float, timezone.utc)
                            if mtime_float > 0
                            else datetime.now(timezone.utc)
                        )
                        new_entry = WorkspaceFileEntry(
                            relative_path=rel_path,
                            absolute_path=full_path,
                            filename=entry,
                            extension=ext,
                            size=size,
                            modified_time=mtime,
                            is_hidden=is_hidden,
                            is_directory=False,
                        )
                        files[rel_path] = new_entry
                        total_size += size

        await asyncio.to_thread(_traverse_incremental, root, 0)

        index_obj = WorkspaceIndex(
            workspace_path=root,
            directories=directories,
            files=files,
            directory_count=len(directories),
            file_count=len(files),
            total_size=total_size,
            maximum_depth=max_depth_reached,
            indexed_at=datetime.now(timezone.utc),
        )
        self._cache[root] = index_obj
        return index_obj
