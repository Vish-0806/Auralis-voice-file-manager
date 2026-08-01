"""Directory Service implementation (Phase 11.2).

Provides directory content listing, safe recursive traversal, tree structure generation,
directory statistics, and empty directory checks.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.exceptions import FileNotFoundError, PathSafetyError
from brain.os.filesystem.filesystem_models import (
    DirectoryMetadata,
    FilesystemEntry,
    FilesystemEntryType,
)
from brain.os.filesystem.interfaces import IDirectoryService, IMetadataService
from brain.os.filesystem.metadata_service import MetadataService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class DirectoryService(IDirectoryService):
    """Provides directory listing, traversal, tree generation, and directory statistics."""

    def __init__(

        self,
        path_service: Optional[IPathService] = None,
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

    def _resolve_and_validate(self, path: str) -> str:
        if not path:
            raise FileNotFoundError("Path cannot be empty", path=path)

        abs_path = self._path_service.resolve_absolute(path)
        if not self._path_service.is_safe_path(abs_path):
            raise PathSafetyError("Directory traversal detected", path=path)

        return abs_path

    def _build_entry(self, entry_path: str) -> FilesystemEntry:
        """Helper to build a FilesystemEntry from a path."""
        st = os.stat(entry_path)
        name = os.path.basename(entry_path) or entry_path
        _, ext = os.path.splitext(name)

        entry_type = FilesystemEntryType.FILE
        if os.path.islink(entry_path):
            entry_type = FilesystemEntryType.SYMLINK
        elif os.path.isdir(entry_path):
            entry_type = FilesystemEntryType.DIRECTORY

        mime = self._metadata_service.get_mime_type(entry_path)
        hidden = self._metadata_service.is_hidden(entry_path)

        created_at = datetime.fromtimestamp(st.st_ctime, timezone.utc)
        modified_at = datetime.fromtimestamp(st.st_mtime, timezone.utc)
        accessed_at = datetime.fromtimestamp(st.st_atime, timezone.utc)

        return FilesystemEntry(
            path=entry_path,
            name=name,
            entry_type=entry_type,
            size_bytes=st.st_size if entry_type == FilesystemEntryType.FILE else 0,
            is_hidden=hidden,
            is_readonly=not bool(st.st_mode & 0o200),
            created_at=created_at,
            modified_at=modified_at,
            accessed_at=accessed_at,
            extension=ext,
            mime_type=mime,
        )

    def list_directory(self, path: str) -> List[FilesystemEntry]:
        """List immediate child entries of a directory."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Directory not found: {abs_path}", path=path)
        if not os.path.isdir(abs_path):
            raise FileNotFoundError(f"Path is not a directory: {abs_path}", path=path)

        results: List[FilesystemEntry] = []
        try:
            for child_name in os.listdir(abs_path):
                child_path = os.path.join(abs_path, child_name)
                try:
                    results.append(self._build_entry(child_path))
                except Exception:
                    pass
        except Exception as e:
            raise FileNotFoundError(f"Failed to list directory {abs_path}: {e}", path=path)

        return results

    def traverse_directory(
        self, path: str, recursive: bool = True, max_depth: int = -1
    ) -> List[FilesystemEntry]:
        """Traverse directory safely with optional depth limiting."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
            raise FileNotFoundError(f"Directory not found: {abs_path}", path=path)

        results: List[FilesystemEntry] = []

        def _walk(current_dir: str, current_depth: int) -> None:
            if max_depth >= 0 and current_depth > max_depth:
                return

            try:
                children = os.listdir(current_dir)
            except Exception:
                return

            for child in children:
                child_path = os.path.join(current_dir, child)
                if not self._path_service.is_safe_path(child_path, base_dir=abs_path):
                    continue

                try:
                    entry = self._build_entry(child_path)
                    results.append(entry)
                    if recursive and entry.entry_type == FilesystemEntryType.DIRECTORY:
                        _walk(child_path, current_depth + 1)
                except Exception:
                    pass

        _walk(abs_path, current_depth=1)
        return results

    def get_directory_statistics(self, path: str) -> DirectoryMetadata:
        """Get aggregate statistics for a directory."""
        return self._metadata_service.get_directory_metadata(path)

    def generate_tree(self, path: str, max_depth: int = 3) -> Dict[str, Any]:
        """Generate hierarchical tree representation of directory."""
        abs_path = self._resolve_and_validate(path)

        def _build_tree_node(dir_path: str, depth: int) -> Dict[str, Any]:
            node_name = os.path.basename(dir_path) or dir_path
            children_nodes: List[Dict[str, Any]] = []

            if depth < max_depth:
                try:
                    for child_name in sorted(os.listdir(dir_path)):
                        child_path = os.path.join(dir_path, child_name)
                        if os.path.isdir(child_path) and not os.path.islink(child_path):
                            children_nodes.append(_build_tree_node(child_path, depth + 1))
                        else:
                            children_nodes.append({
                                "name": child_name,
                                "path": child_path,
                                "type": "file" if os.path.isfile(child_path) else "symlink",
                            })
                except Exception:
                    pass

            return {
                "name": node_name,
                "path": dir_path,
                "type": "directory",
                "children": children_nodes,
            }

        return _build_tree_node(abs_path, depth=0)

    def is_empty(self, path: str) -> bool:
        """Check if directory contains zero child entries."""
        abs_path = self._resolve_and_validate(path)
        if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
            raise FileNotFoundError(f"Directory not found: {abs_path}", path=path)

        try:
            return len(os.listdir(abs_path)) == 0
        except Exception:
            return True
