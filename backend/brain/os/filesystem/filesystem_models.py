"""Filesystem Subsystem Domain Models for Auralis (Phase 11.2).

Defines immutable Pydantic v2 models and enums representing filesystem entries,
file/directory metadata, permission inspection, runtime statistics, search results,
transaction records, health status, operation results, and filesystem capabilities.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class FilesystemEntryType(str, Enum):
    """Type of filesystem entry."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


class PermissionType(str, Enum):
    """Types of filesystem permissions."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    OWNER = "owner"
    GROUP = "group"
    OTHER = "other"


class OperationStatus(str, Enum):
    """Status of filesystem operation or transaction."""

    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PENDING = "pending"
    RUNNING = "running"


class FilesystemEntry(BaseModel):
    """Immutable representation of a filesystem entry."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    name: str = ""
    entry_type: FilesystemEntryType = FilesystemEntryType.UNKNOWN
    size_bytes: int = 0
    is_hidden: bool = False
    is_readonly: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None
    extension: str = ""
    mime_type: str = "application/octet-stream"


class FileMetadata(BaseModel):
    """Immutable detailed metadata for a file."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    name: str = ""
    size_bytes: int = 0
    extension: str = ""
    mime_type: str = "application/octet-stream"
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None
    is_hidden: bool = False
    is_readonly: bool = False
    is_symlink: bool = False
    symlink_target: Optional[str] = None
    owner: str = ""
    group: str = ""
    permissions_summary: str = ""


class DirectoryMetadata(BaseModel):
    """Immutable detailed metadata for a directory."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    name: str = ""
    child_count: int = 0
    total_size_bytes: int = 0
    is_empty: bool = True
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    is_hidden: bool = False
    is_readonly: bool = False
    permissions_summary: str = ""


class PermissionInfo(BaseModel):
    """Immutable permission inspection record for a path."""

    model_config = ConfigDict(frozen=True)

    path: str = ""
    can_read: bool = True
    can_write: bool = True
    can_execute: bool = False
    can_delete: bool = True
    owner: str = ""
    group: str = ""
    permissions_mode: str = ""


class FilesystemStatistics(BaseModel):
    """Immutable performance and usage metrics for the filesystem runtime."""

    model_config = ConfigDict(frozen=True)

    total_operations: int = 0
    reads_count: int = 0
    writes_count: int = 0
    deletes_count: int = 0
    searches_count: int = 0
    bytes_read: int = 0
    bytes_written: int = 0
    errors_count: int = 0
    average_latency_ms: float = 0.0


class SearchResult(BaseModel):
    """Immutable result of a search query across the filesystem."""

    model_config = ConfigDict(frozen=True)

    query: str = ""
    total_matches: int = 0
    matches: List[FilesystemEntry] = Field(default_factory=list)
    search_duration_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)


class TransactionRecord(BaseModel):
    """Immutable record of a filesystem transaction."""

    model_config = ConfigDict(frozen=True)

    transaction_id: str = ""
    status: OperationStatus = OperationStatus.PENDING
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    committed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    error: Optional[str] = None


class FilesystemHealth(BaseModel):
    """Immutable health summary of filesystem services and components."""

    model_config = ConfigDict(frozen=True)

    healthy: bool = True
    status: str = "READY"
    components: Dict[str, bool] = Field(default_factory=dict)
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class FilesystemRuntimeStatus(BaseModel):
    """Immutable status report of the Filesystem Runtime."""

    model_config = ConfigDict(frozen=True)

    state: str = "Initializing"
    healthy: bool = True
    provider_registered: bool = False
    total_operations: int = 0
    errors_count: int = 0
    uptime_seconds: float = 0.0


class OperationResult(BaseModel):
    """Immutable result of a specific filesystem operation."""

    model_config = ConfigDict(frozen=True)

    status: OperationStatus = OperationStatus.SUCCESS
    operation_type: str = ""
    source_path: str = ""
    target_path: Optional[str] = None
    bytes_affected: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FilesystemCapabilities(BaseModel):
    """Immutable capabilities report of the underlying host filesystem."""

    model_config = ConfigDict(frozen=True)

    supports_symlinks: bool = True
    supports_permissions: bool = True
    supports_transactions: bool = True
    supports_atomic_writes: bool = True
    supports_posix_permissions: bool = False
    max_path_length: int = 4096
