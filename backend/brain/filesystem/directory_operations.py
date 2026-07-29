"""Directory Operations for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe directory-level operations.
All operations return immutable OperationResult snapshots.
"""

import logging
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from brain.filesystem.filesystem_models import (
    DirectoryMetadata,
    FilesystemOperationType,
    OperationResult,
    OperationStatus,
    OverwritePolicy,
)
from brain.filesystem.permission_manager import PermissionManager

logger = logging.getLogger(__name__)


class DirectoryOperations:
    """Thread-safe directory-level operations.

    All public methods return :class:`OperationResult` and never raise
    uncaught exceptions.
    """

    def __init__(self, permission_manager: Optional[PermissionManager] = None) -> None:
        """Initializes DirectoryOperations.

        Args:
            permission_manager: Optional shared permission manager.
        """
        self._lock = threading.RLock()
        self._permissions = permission_manager or PermissionManager()

    # ------------------------------------------------------------------
    # Create Directory
    # ------------------------------------------------------------------

    def create_directory(
        self,
        path: str,
        parents: bool = True,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Create a directory (and optional parents).

        Args:
            path: Absolute path of the directory to create.
            parents: If True, create all missing intermediate directories.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: CREATE_DIRECTORY op_id=%s path=%s", op_id, path)

        with self._lock:
            try:
                p = Path(path)
                if p.exists():
                    duration = (time.monotonic() - t0) * 1000
                    return OperationResult(
                        operation_id=op_id,
                        operation_type=FilesystemOperationType.CREATE_DIRECTORY,
                        status=OperationStatus.COMPLETED,
                        source_path=path,
                        output={"already_existed": True},
                        duration_ms=duration,
                        started_at=started,
                        finished_at=datetime.now(timezone.utc),
                    )

                p.mkdir(parents=parents, exist_ok=True)
                self._permissions.invalidate(path)
                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: CREATE_DIRECTORY op_id=%s", op_id)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.CREATE_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: CREATE_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.CREATE_DIRECTORY, path, None, started, str(exc), t0)

    # ------------------------------------------------------------------
    # Delete Directory
    # ------------------------------------------------------------------

    def delete_directory(
        self,
        path: str,
        recursive: bool = False,
        safe: bool = True,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Delete a directory.

        Args:
            path: Absolute path of the directory.
            recursive: If True, remove all contents recursively.
            safe: If True, refuse to delete a non-empty directory unless recursive=True.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: DELETE_DIRECTORY op_id=%s path=%s recursive=%s", op_id, path, recursive)

        with self._lock:
            try:
                p = Path(path)

                if not p.exists():
                    return _fail(op_id, FilesystemOperationType.DELETE_DIRECTORY, path, None, started,
                                 f"Directory does not exist: {path}", t0)

                if not p.is_dir():
                    return _fail(op_id, FilesystemOperationType.DELETE_DIRECTORY, path, None, started,
                                 f"Path is not a directory: {path}", t0)

                # Safety: refuse recursive delete if safe=True and non-empty
                children = list(p.iterdir())
                if children and not recursive:
                    return _fail(op_id, FilesystemOperationType.DELETE_DIRECTORY, path, None, started,
                                 f"Directory is not empty (use recursive=True): {path}", t0)

                if not self._permissions.check_delete(path):
                    logger.warning("Permission Denied: DELETE_DIRECTORY path=%s", path)
                    return _fail(op_id, FilesystemOperationType.DELETE_DIRECTORY, path, None, started,
                                 f"Permission denied: {path}", t0)

                if recursive:
                    shutil.rmtree(str(p))
                else:
                    p.rmdir()

                self._permissions.invalidate(path)
                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: DELETE_DIRECTORY op_id=%s", op_id)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.DELETE_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: DELETE_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.DELETE_DIRECTORY, path, None, started, str(exc), t0)

    # ------------------------------------------------------------------
    # Rename Directory
    # ------------------------------------------------------------------

    def rename_directory(
        self,
        path: str,
        new_name: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Rename a directory within its parent.

        Args:
            path: Absolute path of the directory.
            new_name: New directory name (not a full path).
            overwrite_policy: Conflict resolution policy.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: RENAME_DIRECTORY op_id=%s path=%s new_name=%s", op_id, path, new_name)

        with self._lock:
            try:
                src = Path(path)
                dst = src.parent / new_name
                destination = str(dst)

                if not src.exists() or not src.is_dir():
                    return _fail(op_id, FilesystemOperationType.RENAME_DIRECTORY, path, destination, started,
                                 f"Source directory does not exist: {path}", t0)

                if dst.exists():
                    if overwrite_policy == OverwritePolicy.DENY:
                        return _fail(op_id, FilesystemOperationType.RENAME_DIRECTORY, path, destination, started,
                                     f"Destination already exists: {dst}", t0)

                src.rename(dst)
                self._permissions.invalidate(path)
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: RENAME_DIRECTORY op_id=%s dst=%s", op_id, destination)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.RENAME_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    destination_path=destination,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: RENAME_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.RENAME_DIRECTORY, path, None, started, str(exc), t0)

    # ------------------------------------------------------------------
    # Move Directory
    # ------------------------------------------------------------------

    def move_directory(
        self,
        source: str,
        destination: str,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Move a directory to a new location.

        Args:
            source: Absolute source path.
            destination: Absolute destination path.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: MOVE_DIRECTORY op_id=%s src=%s dst=%s", op_id, source, destination)

        with self._lock:
            try:
                src = Path(source)
                dst = Path(destination)

                if not src.exists() or not src.is_dir():
                    return _fail(op_id, FilesystemOperationType.MOVE_DIRECTORY, source, destination, started,
                                 f"Source directory does not exist: {source}", t0)

                if dst.exists():
                    return _fail(op_id, FilesystemOperationType.MOVE_DIRECTORY, source, destination, started,
                                 f"Destination already exists: {destination}", t0)

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                self._permissions.invalidate(source)
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: MOVE_DIRECTORY op_id=%s", op_id)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.MOVE_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=source,
                    destination_path=destination,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: MOVE_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.MOVE_DIRECTORY, source, destination, started, str(exc), t0)

    # ------------------------------------------------------------------
    # Copy Directory
    # ------------------------------------------------------------------

    def copy_directory(
        self,
        source: str,
        destination: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Copy a directory tree to *destination*.

        Args:
            source: Absolute source path.
            destination: Absolute destination path.
            overwrite_policy: Conflict resolution policy.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: COPY_DIRECTORY op_id=%s src=%s dst=%s", op_id, source, destination)

        with self._lock:
            try:
                src = Path(source)
                dst = Path(destination)

                if not src.exists() or not src.is_dir():
                    return _fail(op_id, FilesystemOperationType.COPY_DIRECTORY, source, destination, started,
                                 f"Source directory does not exist: {source}", t0)

                if dst.exists():
                    if overwrite_policy == OverwritePolicy.DENY:
                        return _fail(op_id, FilesystemOperationType.COPY_DIRECTORY, source, destination, started,
                                     f"Destination already exists: {destination}", t0)
                    if overwrite_policy == OverwritePolicy.SKIP:
                        duration = (time.monotonic() - t0) * 1000
                        return OperationResult(
                            operation_id=op_id,
                            operation_type=FilesystemOperationType.COPY_DIRECTORY,
                            status=OperationStatus.SKIPPED,
                            source_path=source,
                            destination_path=destination,
                            duration_ms=duration,
                            started_at=started,
                            finished_at=datetime.now(timezone.utc),
                        )
                    shutil.rmtree(str(dst))

                shutil.copytree(str(src), str(dst))
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: COPY_DIRECTORY op_id=%s", op_id)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.COPY_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=source,
                    destination_path=destination,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: COPY_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.COPY_DIRECTORY, source, destination, started, str(exc), t0)

    # ------------------------------------------------------------------
    # Empty Directory
    # ------------------------------------------------------------------

    def empty_directory(
        self,
        path: str,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Remove all contents of a directory without deleting the directory itself.

        Args:
            path: Absolute path of the directory to empty.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: EMPTY_DIRECTORY op_id=%s path=%s", op_id, path)

        with self._lock:
            try:
                p = Path(path)

                if not p.exists() or not p.is_dir():
                    return _fail(op_id, FilesystemOperationType.EMPTY_DIRECTORY, path, None, started,
                                 f"Directory does not exist: {path}", t0)

                count = 0
                for child in list(p.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(str(child))
                    else:
                        child.unlink()
                    count += 1

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: EMPTY_DIRECTORY op_id=%s removed=%d", op_id, count)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.EMPTY_DIRECTORY,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    output={"items_removed": count},
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: EMPTY_DIRECTORY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.EMPTY_DIRECTORY, path, None, started, str(exc), t0)

    # ------------------------------------------------------------------
    # List Directory
    # ------------------------------------------------------------------

    def list_directory(
        self,
        path: str,
        recursive: bool = False,
    ) -> List[str]:
        """Return a sorted list of paths inside *path*.

        Args:
            path: Absolute path of the directory to list.
            recursive: If True, include all descendant paths.

        Returns:
            Sorted list of absolute path strings.
        """
        with self._lock:
            try:
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return []

                if recursive:
                    return sorted(str(child) for child in p.rglob("*"))
                return sorted(str(child) for child in p.iterdir())
            except Exception as exc:
                logger.warning("DirectoryOperations.list_directory error path=%s: %s", path, exc)
                return []

    # ------------------------------------------------------------------
    # Read Metadata
    # ------------------------------------------------------------------

    def read_metadata(self, path: str) -> DirectoryMetadata:
        """Return an immutable :class:`DirectoryMetadata` snapshot.

        Args:
            path: Absolute path of the directory.

        Returns:
            Immutable :class:`DirectoryMetadata`.
        """
        with self._lock:
            try:
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return DirectoryMetadata(path=path, name=p.name)

                stat = p.stat()
                children = list(p.iterdir())
                total_size = sum(
                    c.stat().st_size for c in p.rglob("*") if c.is_file()
                )
                return DirectoryMetadata(
                    name=p.name,
                    path=str(p),
                    child_count=len(children),
                    total_size_bytes=total_size,
                    is_hidden=p.name.startswith("."),
                    is_symlink=p.is_symlink(),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    created_at=datetime.fromtimestamp(
                        stat.st_ctime if os.name == "nt" else stat.st_mtime, tz=timezone.utc
                    ),
                )
            except Exception as exc:
                logger.warning("DirectoryOperations.read_metadata error path=%s: %s", path, exc)
                return DirectoryMetadata(path=path)


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return f"dop-{uuid.uuid4().hex[:8]}"


def _fail(
    op_id: str,
    op_type: FilesystemOperationType,
    source: str,
    destination: Optional[str],
    started: datetime,
    error: str,
    t0: float,
) -> OperationResult:
    duration = (time.monotonic() - t0) * 1000
    return OperationResult(
        operation_id=op_id,
        operation_type=op_type,
        status=OperationStatus.FAILED,
        source_path=source,
        destination_path=destination,
        error=error,
        duration_ms=duration,
        started_at=started,
        finished_at=datetime.now(timezone.utc),
    )
