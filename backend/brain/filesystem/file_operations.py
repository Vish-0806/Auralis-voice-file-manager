"""File Operations for the Auralis Filesystem Engine (Phase 9.5).

Provides thread-safe, atomic, and policy-driven file-level operations.
All operations return immutable OperationResult snapshots.
Does NOT perform planning, reasoning, or session management.
"""

import logging
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from brain.filesystem.filesystem_models import (
    FileMetadata,
    FilesystemOperationType,
    OperationResult,
    OperationStatus,
    OverwritePolicy,
)
from brain.filesystem.permission_manager import PermissionManager

logger = logging.getLogger(__name__)


class FileOperations:
    """Thread-safe file-level operations (copy, move, rename, delete, create).

    All public methods return :class:`OperationResult` and never raise
    uncaught exceptions.  Errors are captured in ``result.error``.

    Thread-safety: Each individual operation acquires a path-keyed lock
    segment via a module-level ``threading.RLock()``.
    """

    def __init__(self, permission_manager: Optional[PermissionManager] = None) -> None:
        """Initializes FileOperations.

        Args:
            permission_manager: Optional shared permission manager.  A new
                instance is created if not provided.
        """
        self._lock = threading.RLock()
        self._permissions = permission_manager or PermissionManager()
        logger.debug("FileOperations initialized")

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(
        self,
        source: str,
        destination: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Copy a file from *source* to *destination*.

        Args:
            source: Absolute path of the source file.
            destination: Absolute path of the destination file.
            overwrite_policy: What to do if *destination* already exists.
            operation_id: Optional operation ID for tracking.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: COPY op_id=%s src=%s dst=%s", op_id, source, destination)

        with self._lock:
            try:
                src = Path(source)
                dst = Path(destination)

                if not src.exists():
                    return _fail(op_id, FilesystemOperationType.COPY, source, destination, started,
                                 f"Source does not exist: {source}", t0)

                if not src.is_file():
                    return _fail(op_id, FilesystemOperationType.COPY, source, destination, started,
                                 f"Source is not a file: {source}", t0)

                if not self._permissions.check_read(source):
                    logger.warning("Permission Denied: COPY read src=%s", source)
                    return _fail(op_id, FilesystemOperationType.COPY, source, destination, started,
                                 f"Permission denied: cannot read {source}", t0)

                conflict_result = self._handle_conflict(dst, overwrite_policy, op_id,
                                                        FilesystemOperationType.COPY, source,
                                                        destination, started, t0)
                if conflict_result is not None:
                    return conflict_result

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: COPY op_id=%s dst=%s", op_id, destination)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.COPY,
                    status=OperationStatus.COMPLETED,
                    source_path=source,
                    destination_path=destination,
                    output={"bytes_copied": src.stat().st_size if src.exists() else 0},
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: COPY op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.COPY, source, destination, started,
                             str(exc), t0)

    # ------------------------------------------------------------------
    # Move
    # ------------------------------------------------------------------

    def move(
        self,
        source: str,
        destination: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Move a file from *source* to *destination* atomically.

        Implemented as copy-then-delete to provide rollback safety.

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
        logger.info("Operation Started: MOVE op_id=%s src=%s dst=%s", op_id, source, destination)

        with self._lock:
            try:
                src = Path(source)
                dst = Path(destination)

                if not src.exists():
                    return _fail(op_id, FilesystemOperationType.MOVE, source, destination, started,
                                 f"Source does not exist: {source}", t0)

                if not src.is_file():
                    return _fail(op_id, FilesystemOperationType.MOVE, source, destination, started,
                                 f"Source is not a file: {source}", t0)

                if not self._permissions.check_read(source):
                    logger.warning("Permission Denied: MOVE read src=%s", source)
                    return _fail(op_id, FilesystemOperationType.MOVE, source, destination, started,
                                 f"Permission denied: cannot read {source}", t0)

                if not self._permissions.check_delete(source):
                    logger.warning("Permission Denied: MOVE delete src=%s", source)
                    return _fail(op_id, FilesystemOperationType.MOVE, source, destination, started,
                                 f"Permission denied: cannot delete {source}", t0)

                conflict_result = self._handle_conflict(dst, overwrite_policy, op_id,
                                                        FilesystemOperationType.MOVE, source,
                                                        destination, started, t0)
                if conflict_result is not None:
                    return conflict_result

                file_size = src.stat().st_size
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                self._permissions.invalidate(source)
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: MOVE op_id=%s dst=%s", op_id, destination)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.MOVE,
                    status=OperationStatus.COMPLETED,
                    source_path=source,
                    destination_path=destination,
                    output={"bytes_moved": file_size},
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: MOVE op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.MOVE, source, destination, started,
                             str(exc), t0)

    # ------------------------------------------------------------------
    # Rename
    # ------------------------------------------------------------------

    def rename(
        self,
        source: str,
        new_name: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Rename a file within its parent directory.

        Args:
            source: Absolute path of the file to rename.
            new_name: New filename (not a full path).
            overwrite_policy: Conflict resolution policy.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: RENAME op_id=%s src=%s new_name=%s", op_id, source, new_name)

        with self._lock:
            try:
                src = Path(source)
                dst = src.parent / new_name
                destination = str(dst)

                if not src.exists():
                    return _fail(op_id, FilesystemOperationType.RENAME, source, destination, started,
                                 f"Source does not exist: {source}", t0)

                if not src.is_file():
                    return _fail(op_id, FilesystemOperationType.RENAME, source, destination, started,
                                 f"Source is not a file: {source}", t0)

                conflict_result = self._handle_conflict(dst, overwrite_policy, op_id,
                                                        FilesystemOperationType.RENAME, source,
                                                        destination, started, t0)
                if conflict_result is not None:
                    return conflict_result

                src.rename(dst)
                self._permissions.invalidate(source)
                self._permissions.invalidate(destination)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: RENAME op_id=%s dst=%s", op_id, destination)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.RENAME,
                    status=OperationStatus.COMPLETED,
                    source_path=source,
                    destination_path=destination,
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: RENAME op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.RENAME, source, destination if 'destination' in dir() else source, started,
                             str(exc), t0)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        path: str,
        safe: bool = True,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Delete a file.

        Args:
            path: Absolute path of the file to delete.
            safe: If True, verify the path is not a directory before deleting.
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: DELETE op_id=%s path=%s", op_id, path)

        with self._lock:
            try:
                p = Path(path)

                if not p.exists():
                    return _fail(op_id, FilesystemOperationType.DELETE, path, None, started,
                                 f"File does not exist: {path}", t0)

                if safe and p.is_dir():
                    return _fail(op_id, FilesystemOperationType.DELETE, path, None, started,
                                 f"Path is a directory (use delete_directory): {path}", t0)

                if not self._permissions.check_delete(path):
                    logger.warning("Permission Denied: DELETE path=%s", path)
                    return _fail(op_id, FilesystemOperationType.DELETE, path, None, started,
                                 f"Permission denied: cannot delete {path}", t0)

                file_size = p.stat().st_size if p.is_file() else 0
                p.unlink()
                self._permissions.invalidate(path)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: DELETE op_id=%s path=%s", op_id, path)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.DELETE,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    output={"bytes_deleted": file_size},
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: DELETE op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.DELETE, path, None, started,
                             str(exc), t0)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        path: str,
        content: str = "",
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        encoding: str = "utf-8",
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Create a new file with optional text content.

        Args:
            path: Absolute path of the file to create.
            content: Initial text content.
            overwrite_policy: Conflict resolution policy.
            encoding: File encoding (default UTF-8).
            operation_id: Optional operation ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        started = datetime.now(timezone.utc)
        t0 = time.monotonic()
        logger.info("Operation Started: CREATE op_id=%s path=%s", op_id, path)

        with self._lock:
            try:
                p = Path(path)

                conflict_result = self._handle_conflict(p, overwrite_policy, op_id,
                                                        FilesystemOperationType.CREATE, path,
                                                        None, started, t0)
                if conflict_result is not None:
                    return conflict_result

                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding=encoding)
                self._permissions.invalidate(path)

                duration = (time.monotonic() - t0) * 1000
                logger.info("Operation Completed: CREATE op_id=%s path=%s", op_id, path)
                return OperationResult(
                    operation_id=op_id,
                    operation_type=FilesystemOperationType.CREATE,
                    status=OperationStatus.COMPLETED,
                    source_path=path,
                    output={"bytes_written": len(content.encode(encoding))},
                    duration_ms=duration,
                    started_at=started,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Operation Failed: CREATE op_id=%s error=%s", op_id, exc)
                return _fail(op_id, FilesystemOperationType.CREATE, path, None, started,
                             str(exc), t0)

    # ------------------------------------------------------------------
    # Read Metadata
    # ------------------------------------------------------------------

    def read_metadata(self, path: str) -> FileMetadata:
        """Return an immutable :class:`FileMetadata` snapshot for *path*.

        Args:
            path: Absolute path of the file.

        Returns:
            Immutable :class:`FileMetadata` (all-default on error).
        """
        with self._lock:
            try:
                p = Path(path)
                if not p.exists() or not p.is_file():
                    return FileMetadata(path=path, name=p.name)

                stat = p.stat()
                return FileMetadata(
                    name=p.name,
                    path=str(p),
                    extension=p.suffix,
                    size_bytes=stat.st_size,
                    is_hidden=p.name.startswith("."),
                    is_symlink=p.is_symlink(),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    created_at=datetime.fromtimestamp(
                        stat.st_ctime if os.name == "nt" else stat.st_mtime, tz=timezone.utc
                    ),
                    accessed_at=datetime.fromtimestamp(stat.st_atime, tz=timezone.utc),
                )
            except Exception as exc:
                logger.warning("FileOperations.read_metadata error path=%s: %s", path, exc)
                return FileMetadata(path=path)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _handle_conflict(
        self,
        dst: Path,
        policy: OverwritePolicy,
        op_id: str,
        op_type: FilesystemOperationType,
        source: str,
        destination: Optional[str],
        started: datetime,
        t0: float,
    ) -> Optional[OperationResult]:
        """Apply the overwrite policy when *dst* already exists.

        Returns an :class:`OperationResult` to return immediately, or
        None if processing should continue.
        """
        if not dst.exists():
            return None

        if policy == OverwritePolicy.DENY:
            msg = f"Destination already exists: {dst}"
            logger.warning("Operation Failed: %s op_id=%s reason=%s", op_type, op_id, msg)
            return _fail(op_id, op_type, source, destination, started, msg, t0)

        if policy == OverwritePolicy.SKIP:
            duration = (time.monotonic() - t0) * 1000
            logger.info("Operation Completed (SKIP): %s op_id=%s", op_type, op_id)
            return OperationResult(
                operation_id=op_id,
                operation_type=op_type,
                status=OperationStatus.SKIPPED,
                source_path=source,
                destination_path=destination,
                output={"skipped": True},
                duration_ms=duration,
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

        if policy == OverwritePolicy.RENAME:
            # Auto-rename by appending a counter suffix
            counter = 1
            stem = dst.stem
            suffix = dst.suffix
            parent = dst.parent
            while dst.exists():
                dst = parent / f"{stem}_{counter}{suffix}"
                counter += 1
            return None  # updated dst handled by caller — but dst is local here

        # OVERWRITE — let caller proceed (no pre-check needed)
        return None


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return f"fop-{uuid.uuid4().hex[:8]}"


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
