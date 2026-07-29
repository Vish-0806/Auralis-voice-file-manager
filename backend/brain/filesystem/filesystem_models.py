"""Immutable data models for the Auralis Filesystem Engine (Phase 9.5).

All models use ConfigDict(frozen=True) for thread-safe, immutable snapshots.
No business logic, no OS interaction, no imports from other filesystem modules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class FilesystemOperationType(str, Enum):
    """Type of filesystem operation being performed."""

    COPY = "COPY"
    MOVE = "MOVE"
    RENAME = "RENAME"
    DELETE = "DELETE"
    CREATE = "CREATE"
    READ = "READ"
    WRITE = "WRITE"
    LIST = "LIST"
    SEARCH = "SEARCH"
    CREATE_DIRECTORY = "CREATE_DIRECTORY"
    DELETE_DIRECTORY = "DELETE_DIRECTORY"
    RENAME_DIRECTORY = "RENAME_DIRECTORY"
    MOVE_DIRECTORY = "MOVE_DIRECTORY"
    COPY_DIRECTORY = "COPY_DIRECTORY"
    EMPTY_DIRECTORY = "EMPTY_DIRECTORY"
    ROLLBACK = "ROLLBACK"


class OperationStatus(str, Enum):
    """Lifecycle status of a single filesystem operation."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ROLLED_BACK = "ROLLED_BACK"


class OverwritePolicy(str, Enum):
    """Policy for handling destination conflicts during copy/move."""

    DENY = "DENY"        # Fail if destination exists
    OVERWRITE = "OVERWRITE"  # Replace destination unconditionally
    SKIP = "SKIP"        # Silently skip if destination exists
    RENAME = "RENAME"    # Auto-rename destination to avoid conflict


class SortField(str, Enum):
    """Sort field for search results."""

    NAME = "NAME"
    SIZE = "SIZE"
    MODIFIED = "MODIFIED"
    CREATED = "CREATED"
    EXTENSION = "EXTENSION"


class SortOrder(str, Enum):
    """Sort direction for search results."""

    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class TransactionStatus(str, Enum):
    """Status of a filesystem transaction."""

    OPEN = "OPEN"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Operation Models
# ---------------------------------------------------------------------------


class FilesystemOperation(BaseModel):
    """Immutable descriptor for a single filesystem operation."""

    model_config = ConfigDict(frozen=True)

    operation_id: str = ""
    operation_type: FilesystemOperationType = FilesystemOperationType.READ
    source_path: str = ""
    destination_path: Optional[str] = None
    overwrite_policy: OverwritePolicy = OverwritePolicy.DENY
    recursive: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OperationResult(BaseModel):
    """Immutable result of a single filesystem operation."""

    model_config = ConfigDict(frozen=True)

    operation_id: str = ""
    operation_type: FilesystemOperationType = FilesystemOperationType.READ
    status: OperationStatus = OperationStatus.COMPLETED
    source_path: str = ""
    destination_path: Optional[str] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Transaction Models
# ---------------------------------------------------------------------------


class Transaction(BaseModel):
    """Immutable record of a pending or active filesystem transaction."""

    model_config = ConfigDict(frozen=True)

    transaction_id: str = ""
    status: TransactionStatus = TransactionStatus.OPEN
    operations: List[FilesystemOperation] = Field(default_factory=list)
    parent_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionResult(BaseModel):
    """Immutable result of a completed or aborted filesystem transaction."""

    model_config = ConfigDict(frozen=True)

    transaction_id: str = ""
    status: TransactionStatus = TransactionStatus.COMMITTED
    operation_results: List[OperationResult] = Field(default_factory=list)
    completed_operations: int = 0
    failed_operations: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Rollback Models
# ---------------------------------------------------------------------------


class RollbackOperation(BaseModel):
    """Immutable inverse operation to undo a completed filesystem operation."""

    model_config = ConfigDict(frozen=True)

    rollback_id: str = ""
    original_operation_id: str = ""
    operation_type: FilesystemOperationType = FilesystemOperationType.ROLLBACK
    source_path: str = ""
    destination_path: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RollbackResult(BaseModel):
    """Immutable result of a rollback execution."""

    model_config = ConfigDict(frozen=True)

    transaction_id: str = ""
    status: OperationStatus = OperationStatus.COMPLETED
    rollback_operations: List[RollbackOperation] = Field(default_factory=list)
    operation_results: List[OperationResult] = Field(default_factory=list)
    completed_rollbacks: int = 0
    failed_rollbacks: int = 0
    partial: bool = False
    error: Optional[str] = None
    duration_ms: float = 0.0
    started_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Metadata Models
# ---------------------------------------------------------------------------


class FileMetadata(BaseModel):
    """Immutable metadata snapshot for a single file."""

    model_config = ConfigDict(frozen=True)

    name: str = ""
    path: str = ""
    extension: str = ""
    size_bytes: int = 0
    is_hidden: bool = False
    is_symlink: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DirectoryMetadata(BaseModel):
    """Immutable metadata snapshot for a directory."""

    model_config = ConfigDict(frozen=True)

    name: str = ""
    path: str = ""
    child_count: int = 0
    total_size_bytes: int = 0
    is_hidden: bool = False
    is_symlink: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Search Models
# ---------------------------------------------------------------------------


class SearchMatch(BaseModel):
    """Immutable record of a single search match."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    name: str = ""
    extension: str = ""
    size_bytes: int = 0
    modified_at: Optional[datetime] = None
    is_directory: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Immutable result of a filesystem search query."""

    model_config = ConfigDict(frozen=True)

    query: str = ""
    root_path: str = ""
    matches: List[SearchMatch] = Field(default_factory=list)
    total_matches: int = 0
    page: int = 1
    page_size: int = 100
    total_pages: int = 1
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Permission Models
# ---------------------------------------------------------------------------


class PermissionResult(BaseModel):
    """Immutable record of filesystem permission check results."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_execute: bool = False
    is_directory: bool = False
    exists: bool = False
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Runtime / Health Models
# ---------------------------------------------------------------------------


class FilesystemHealth(BaseModel):
    """Immutable runtime health snapshot for the Filesystem Engine."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    registered_components: List[str] = Field(default_factory=list)
    uptime_seconds: float = 0.0
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FilesystemStatistics(BaseModel):
    """Immutable snapshot of runtime statistics for the Filesystem Engine."""

    model_config = ConfigDict(frozen=True)

    operations_started: int = 0
    operations_completed: int = 0
    operations_failed: int = 0
    transactions_started: int = 0
    transactions_committed: int = 0
    transactions_aborted: int = 0
    rollbacks_performed: int = 0
    bytes_copied: int = 0
    bytes_moved: int = 0
    bytes_deleted: int = 0
    searches_performed: int = 0
    average_operation_ms: float = 0.0
    peak_concurrent_operations: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
