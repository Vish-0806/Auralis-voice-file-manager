"""Filesystem Engine subsystem package for Auralis (Phase 9.5)."""

from __future__ import annotations

from .directory_operations import DirectoryOperations
from .file_operations import FileOperations
from .filesystem_models import (
    DirectoryMetadata,
    FileMetadata,
    FilesystemHealth,
    FilesystemOperation,
    FilesystemOperationType,
    FilesystemStatistics,
    OperationResult,
    OperationStatus,
    OverwritePolicy,
    PermissionResult,
    RollbackOperation,
    RollbackResult,
    SearchMatch,
    SearchResult,
    SortField,
    SortOrder,
    Transaction,
    TransactionResult,
    TransactionStatus,
)
from .filesystem_provider import FilesystemProvider
from .path_resolver import PathResolver
from .permission_manager import PermissionManager
from .rollback_manager import RollbackManager
from .runtime import (
    FilesystemRuntimeCoordinator,
    FilesystemRuntimeStatus,
    get_filesystem_runtime,
    reset_filesystem_runtime,
)
from .search_engine import SearchEngine
from .transaction_manager import TransactionManager

__all__ = [
    # Models
    "FilesystemOperationType",
    "OperationStatus",
    "OverwritePolicy",
    "SortField",
    "SortOrder",
    "TransactionStatus",
    "FilesystemOperation",
    "OperationResult",
    "Transaction",
    "TransactionResult",
    "RollbackOperation",
    "RollbackResult",
    "FileMetadata",
    "DirectoryMetadata",
    "SearchMatch",
    "SearchResult",
    "PermissionResult",
    "FilesystemHealth",
    "FilesystemStatistics",
    # Components
    "PathResolver",
    "PermissionManager",
    "FileOperations",
    "DirectoryOperations",
    "SearchEngine",
    "TransactionManager",
    "RollbackManager",
    "FilesystemProvider",
    # Runtime
    "FilesystemRuntimeStatus",
    "FilesystemRuntimeCoordinator",
    "get_filesystem_runtime",
    "reset_filesystem_runtime",
]
