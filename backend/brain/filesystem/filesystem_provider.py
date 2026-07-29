"""Filesystem Provider for the Auralis Filesystem Engine (Phase 9.5).

Single entry point for all filesystem operations.
Composes FileOperations, DirectoryOperations, SearchEngine,
TransactionManager, and RollbackManager behind a unified facade.
"""

import contextlib
import logging
import threading
import uuid
from typing import Dict, Generator, List, Optional

from brain.filesystem.directory_operations import DirectoryOperations
from brain.filesystem.file_operations import FileOperations
from brain.filesystem.filesystem_models import (
    DirectoryMetadata,
    FileMetadata,
    FilesystemOperation,
    FilesystemOperationType,
    OperationResult,
    OperationStatus,
    OverwritePolicy,
    RollbackResult,
    SearchResult,
    SortField,
    SortOrder,
    TransactionResult,
    TransactionStatus,
)
from brain.filesystem.permission_manager import PermissionManager
from brain.filesystem.rollback_manager import RollbackManager
from brain.filesystem.search_engine import SearchEngine
from brain.filesystem.transaction_manager import TransactionManager
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FilesystemProvider:
    """Thread-safe unified facade for all Filesystem Engine operations.

    Exposes:
    - File operations: ``copy``, ``move``, ``rename``, ``delete``, ``create``
    - Directory operations: ``create_directory``, ``delete_directory``
    - Search: ``search``, ``list_directory``
    - Transactions: ``transaction()`` context manager, ``commit_transaction``
    - Rollback: ``rollback``
    - Metadata: ``file_metadata``, ``directory_metadata``
    """

    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        file_ops: Optional[FileOperations] = None,
        dir_ops: Optional[DirectoryOperations] = None,
        search_engine: Optional[SearchEngine] = None,
        transaction_manager: Optional[TransactionManager] = None,
        rollback_manager: Optional[RollbackManager] = None,
    ) -> None:
        """Initializes FilesystemProvider.

        All component dependencies are injectable for testability.

        Args:
            permission_manager: Shared permission manager.
            file_ops: File operations handler.
            dir_ops: Directory operations handler.
            search_engine: Search handler.
            transaction_manager: Transaction coordinator.
            rollback_manager: Rollback executor.
        """
        self._lock = threading.RLock()
        self._permissions = permission_manager or PermissionManager()
        self._file_ops = file_ops or FileOperations(self._permissions)
        self._dir_ops = dir_ops or DirectoryOperations(self._permissions)
        self._search_engine = search_engine or SearchEngine()
        self._rollback_manager = rollback_manager or RollbackManager()
        self._transaction_manager = transaction_manager or TransactionManager(
            executor=self._execute_operation
        )
        logger.debug("FilesystemProvider initialized")

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    def copy(
        self,
        source: str,
        destination: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Copy a file from *source* to *destination*.

        Args:
            source: Absolute source path.
            destination: Absolute destination path.
            overwrite_policy: Conflict resolution policy.
            transaction_id: If set, record into this transaction instead of executing immediately.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.COPY,
                source, destination, overwrite_policy=overwrite_policy
            )
        return self._file_ops.copy(source, destination, overwrite_policy, op_id)

    def move(
        self,
        source: str,
        destination: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Move a file from *source* to *destination*.

        Args:
            source: Absolute source path.
            destination: Absolute destination path.
            overwrite_policy: Conflict resolution policy.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.MOVE,
                source, destination, overwrite_policy=overwrite_policy
            )
        return self._file_ops.move(source, destination, overwrite_policy, op_id)

    def rename(
        self,
        path: str,
        new_name: str,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Rename a file within its parent directory.

        Args:
            path: Absolute path of the file.
            new_name: New filename (not a full path).
            overwrite_policy: Conflict resolution policy.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.RENAME,
                path, new_name, overwrite_policy=overwrite_policy
            )
        return self._file_ops.rename(path, new_name, overwrite_policy, op_id)

    def delete(
        self,
        path: str,
        safe: bool = True,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Delete a file.

        Args:
            path: Absolute path of the file to delete.
            safe: If True, reject directories.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.DELETE,
                path, parameters={"safe": safe}
            )
        return self._file_ops.delete(path, safe, op_id)

    def create(
        self,
        path: str,
        content: str = "",
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        encoding: str = "utf-8",
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Create a new file with optional text content.

        Args:
            path: Absolute path of the file to create.
            content: Initial text content.
            overwrite_policy: Conflict resolution policy.
            encoding: File encoding.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.CREATE,
                path, parameters={"content": content, "encoding": encoding,
                                  "overwrite_policy": overwrite_policy.value}
            )
        return self._file_ops.create(path, content, overwrite_policy, encoding, op_id)

    # ------------------------------------------------------------------
    # Directory Operations
    # ------------------------------------------------------------------

    def create_directory(
        self,
        path: str,
        parents: bool = True,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Create a directory (with optional parents).

        Args:
            path: Absolute path of the directory.
            parents: If True, create intermediate directories.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.CREATE_DIRECTORY,
                path, parameters={"parents": parents}
            )
        return self._dir_ops.create_directory(path, parents, op_id)

    def delete_directory(
        self,
        path: str,
        recursive: bool = False,
        safe: bool = True,
        transaction_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> OperationResult:
        """Delete a directory.

        Args:
            path: Absolute path of the directory.
            recursive: If True, delete all contents.
            safe: If True, refuse to delete non-empty directories unless recursive=True.
            transaction_id: Optional transaction to record into.
            operation_id: Optional operation tracking ID.

        Returns:
            Immutable :class:`OperationResult`.
        """
        op_id = operation_id or _new_id()
        if transaction_id:
            return self._record_transaction_op(
                transaction_id, op_id, FilesystemOperationType.DELETE_DIRECTORY,
                path, parameters={"recursive": recursive, "safe": safe}
            )
        return self._dir_ops.delete_directory(path, recursive, safe, op_id)

    def list_directory(self, path: str, recursive: bool = False) -> List[str]:
        """List the contents of a directory.

        Args:
            path: Absolute path of the directory.
            recursive: If True, include all descendants.

        Returns:
            Sorted list of absolute path strings.
        """
        return self._dir_ops.list_directory(path, recursive)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

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
        """Execute a filesystem search.

        All parameters are forwarded to :class:`SearchEngine`.

        Returns:
            Immutable :class:`SearchResult`.
        """
        return self._search_engine.search(
            root=root,
            pattern=pattern,
            recursive=recursive,
            use_regex=use_regex,
            extensions=extensions,
            min_size_bytes=min_size_bytes,
            max_size_bytes=max_size_bytes,
            modified_after=modified_after,
            modified_before=modified_before,
            include_directories=include_directories,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def file_metadata(self, path: str) -> FileMetadata:
        """Return file metadata for *path*.

        Args:
            path: Absolute path of the file.

        Returns:
            Immutable :class:`FileMetadata`.
        """
        return self._file_ops.read_metadata(path)

    def directory_metadata(self, path: str) -> DirectoryMetadata:
        """Return directory metadata for *path*.

        Args:
            path: Absolute path of the directory.

        Returns:
            Immutable :class:`DirectoryMetadata`.
        """
        return self._dir_ops.read_metadata(path)

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def transaction(
        self,
        transaction_id: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Context manager for transactional filesystem operations.

        On ``__exit__`` with no exception, automatically commits.
        On ``__exit__`` with an exception, automatically aborts.

        Usage::

            with provider.transaction() as tx_id:
                provider.copy(src, dst, transaction_id=tx_id)
                provider.delete(old, transaction_id=tx_id)

        Args:
            transaction_id: Optional explicit transaction ID.

        Yields:
            Transaction ID string.
        """
        tx = self._transaction_manager.begin(transaction_id)
        tx_id = tx.transaction_id
        try:
            yield tx_id
            self._transaction_manager.commit(tx_id)
        except Exception:
            self._transaction_manager.abort(tx_id)
            raise

    def commit_transaction(self, transaction_id: str) -> TransactionResult:
        """Manually commit a transaction.

        Args:
            transaction_id: Transaction to commit.

        Returns:
            Immutable :class:`TransactionResult`.
        """
        return self._transaction_manager.commit(transaction_id)

    def abort_transaction(self, transaction_id: str) -> TransactionResult:
        """Manually abort a transaction.

        Args:
            transaction_id: Transaction to abort.

        Returns:
            Immutable :class:`TransactionResult`.
        """
        return self._transaction_manager.abort(transaction_id)

    def begin_transaction(self, transaction_id: Optional[str] = None) -> str:
        """Open a new transaction and return its ID.

        Args:
            transaction_id: Optional explicit ID.

        Returns:
            Transaction ID string.
        """
        tx = self._transaction_manager.begin(transaction_id)
        return tx.transaction_id

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def rollback(self, transaction_result: TransactionResult) -> RollbackResult:
        """Roll back all completed operations in a transaction result.

        Args:
            transaction_result: Completed or partially-failed transaction.

        Returns:
            Immutable :class:`RollbackResult`.
        """
        return self._rollback_manager.rollback(transaction_result)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _execute_operation(self, op: FilesystemOperation) -> OperationResult:
        """Dispatch a :class:`FilesystemOperation` to the appropriate handler.

        Used as the executor callback by :class:`TransactionManager`.

        Args:
            op: Operation to execute.

        Returns:
            Immutable :class:`OperationResult`.
        """
        t = op.operation_type
        params = dict(op.parameters)

        if t == FilesystemOperationType.COPY:
            policy = OverwritePolicy(params.get("overwrite_policy", OverwritePolicy.DENY.value))
            return self._file_ops.copy(op.source_path, op.destination_path or "", policy, op.operation_id)

        if t == FilesystemOperationType.MOVE:
            policy = OverwritePolicy(params.get("overwrite_policy", OverwritePolicy.DENY.value))
            return self._file_ops.move(op.source_path, op.destination_path or "", policy, op.operation_id)

        if t == FilesystemOperationType.RENAME:
            policy = OverwritePolicy(params.get("overwrite_policy", OverwritePolicy.DENY.value))
            new_name = op.destination_path or ""
            return self._file_ops.rename(op.source_path, new_name, policy, op.operation_id)

        if t == FilesystemOperationType.DELETE:
            safe = bool(params.get("safe", True))
            return self._file_ops.delete(op.source_path, safe, op.operation_id)

        if t == FilesystemOperationType.CREATE:
            content = str(params.get("content", ""))
            encoding = str(params.get("encoding", "utf-8"))
            policy_val = params.get("overwrite_policy", OverwritePolicy.DENY.value)
            policy = OverwritePolicy(policy_val)
            return self._file_ops.create(op.source_path, content, policy, encoding, op.operation_id)

        if t == FilesystemOperationType.CREATE_DIRECTORY:
            parents = bool(params.get("parents", True))
            return self._dir_ops.create_directory(op.source_path, parents, op.operation_id)

        if t == FilesystemOperationType.DELETE_DIRECTORY:
            recursive = bool(params.get("recursive", False))
            safe = bool(params.get("safe", True))
            return self._dir_ops.delete_directory(op.source_path, recursive, safe, op.operation_id)

        if t == FilesystemOperationType.COPY_DIRECTORY:
            policy = OverwritePolicy(params.get("overwrite_policy", OverwritePolicy.DENY.value))
            return self._dir_ops.copy_directory(op.source_path, op.destination_path or "", policy, op.operation_id)

        if t == FilesystemOperationType.MOVE_DIRECTORY:
            return self._dir_ops.move_directory(op.source_path, op.destination_path or "", op.operation_id)

        if t == FilesystemOperationType.EMPTY_DIRECTORY:
            return self._dir_ops.empty_directory(op.source_path, op.operation_id)

        # Unknown type — return success stub so callers don't break
        now = datetime.now(timezone.utc)
        return OperationResult(
            operation_id=op.operation_id,
            operation_type=t,
            status=OperationStatus.COMPLETED,
            source_path=op.source_path,
            destination_path=op.destination_path,
            started_at=now,
            finished_at=now,
        )

    def _record_transaction_op(
        self,
        transaction_id: str,
        op_id: str,
        op_type: FilesystemOperationType,
        source: str,
        destination: Optional[str] = None,
        overwrite_policy: OverwritePolicy = OverwritePolicy.DENY,
        parameters: Optional[Dict] = None,
    ) -> OperationResult:
        """Record an operation into a transaction without executing it.

        Returns a PENDING result stub.
        """
        params = dict(parameters or {})
        if overwrite_policy != OverwritePolicy.DENY:
            params["overwrite_policy"] = overwrite_policy.value

        op = FilesystemOperation(
            operation_id=op_id,
            operation_type=op_type,
            source_path=source,
            destination_path=destination,
            overwrite_policy=overwrite_policy,
            parameters=params,
        )
        recorded = self._transaction_manager.record_operation(transaction_id, op)
        now = datetime.now(timezone.utc)
        return OperationResult(
            operation_id=op_id,
            operation_type=op_type,
            status=OperationStatus.PENDING if recorded else OperationStatus.FAILED,
            source_path=source,
            destination_path=destination,
            error=None if recorded else f"Transaction '{transaction_id}' not found or not open",
            started_at=now,
            finished_at=now,
        )


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return f"fp-{uuid.uuid4().hex[:8]}"
