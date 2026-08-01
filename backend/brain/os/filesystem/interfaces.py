"""Abstract interfaces for the Filesystem Subsystem (Phase 11.2).

Defines canonical interfaces for Permission Inspection, Metadata Service,
Directory Service, File Service, Search Service, Transaction Runtime,
Filesystem Provider, and Filesystem Runtime.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from brain.os.filesystem.filesystem_models import (
    DirectoryMetadata,
    FileMetadata,
    FilesystemCapabilities,
    FilesystemEntry,
    FilesystemHealth,
    FilesystemRuntimeStatus,
    FilesystemStatistics,
    OperationResult,
    PermissionInfo,
    SearchResult,
    TransactionRecord,
)


class IPermissionService(ABC):
    """Interface for read-only permission and ownership inspection."""

    @abstractmethod
    def check_permissions(self, path: str) -> PermissionInfo:
        """Inspect and return permission info for a path."""
        pass

    @abstractmethod
    def can_read(self, path: str) -> bool:
        """Check if path is readable."""
        pass

    @abstractmethod
    def can_write(self, path: str) -> bool:
        """Check if path is writable."""
        pass

    @abstractmethod
    def can_execute(self, path: str) -> bool:
        """Check if path is executable."""
        pass

    @abstractmethod
    def can_delete(self, path: str) -> bool:
        """Check if path can be deleted."""
        pass


class IMetadataService(ABC):
    """Interface for inspecting file and directory metadata."""

    @abstractmethod
    def get_file_metadata(self, path: str) -> FileMetadata:
        """Extract detailed metadata for a file."""
        pass

    @abstractmethod
    def get_directory_metadata(self, path: str) -> DirectoryMetadata:
        """Extract detailed metadata for a directory."""
        pass

    @abstractmethod
    def get_mime_type(self, path: str) -> str:
        """Determine MIME content type of a file."""
        pass

    @abstractmethod
    def is_hidden(self, path: str) -> bool:
        """Check if file or directory is hidden."""
        pass

    @abstractmethod
    def is_symlink(self, path: str) -> bool:
        """Check if path is a symbolic link."""
        pass


class IDirectoryService(ABC):
    """Interface for directory listing, traversal, tree generation, and stats."""

    @abstractmethod
    def list_directory(self, path: str) -> List[FilesystemEntry]:
        """List immediate child entries of a directory."""
        pass

    @abstractmethod
    def traverse_directory(
        self, path: str, recursive: bool = True, max_depth: int = -1
    ) -> List[FilesystemEntry]:
        """Traverse directory safely with optional depth limiting."""
        pass

    @abstractmethod
    def get_directory_statistics(self, path: str) -> DirectoryMetadata:
        """Get aggregate statistics for a directory."""
        pass

    @abstractmethod
    def generate_tree(self, path: str, max_depth: int = 3) -> Dict[str, Any]:
        """Generate hierarchical tree representation of directory."""
        pass

    @abstractmethod
    def is_empty(self, path: str) -> bool:
        """Check if directory contains zero child entries."""
        pass


class IFileService(ABC):
    """Interface for safe file read, write, copy, move, rename, and delete operations."""

    @abstractmethod
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        pass

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """Read raw bytes from a file."""
        pass

    @abstractmethod
    def write_text(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = True,
        overwrite: bool = True,
    ) -> OperationResult:
        """Write text to file with optional atomic swap and overwrite policy."""
        pass

    @abstractmethod
    def write_bytes(
        self,
        path: str,
        data: bytes,
        atomic: bool = True,
        overwrite: bool = True,
    ) -> OperationResult:
        """Write bytes to file with optional atomic swap and overwrite policy."""
        pass

    @abstractmethod
    def copy_file(
        self, source: str, destination: str, overwrite: bool = True
    ) -> OperationResult:
        """Copy file from source to destination."""
        pass

    @abstractmethod
    def move_file(
        self, source: str, destination: str, overwrite: bool = True
    ) -> OperationResult:
        """Move file from source to destination."""
        pass

    @abstractmethod
    def rename_file(self, path: str, new_name: str) -> OperationResult:
        """Rename a file or directory in place."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> OperationResult:
        """Delete a file or empty directory."""
        pass


class IFilesystemSearchService(ABC):
    """Interface for searching files and directories by query, pattern, size, and date."""

    @abstractmethod
    def search(
        self,
        root_path: str,
        query: str = "",
        pattern: Optional[str] = None,
        extension: Optional[str] = None,
        regex: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None,
        recursive: bool = True,
        case_sensitive: bool = False,
        include_hidden: bool = False,
    ) -> SearchResult:
        """Perform search across filesystem tree matching criteria."""
        pass


class IFilesystemTransactionRuntime(ABC):
    """Interface for tracking filesystem transactions, logging operations, and rollback."""

    @abstractmethod
    def begin_transaction(self) -> str:
        """Begin a new transaction and return transaction ID."""
        pass

    @abstractmethod
    def record_operation(
        self,
        transaction_id: str,
        operation_type: str,
        source_path: str,
        target_path: Optional[str] = None,
        backup_path: Optional[str] = None,
    ) -> None:
        """Record an operation step under an active transaction."""
        pass

    @abstractmethod
    def commit_transaction(self, transaction_id: str) -> TransactionRecord:
        """Commit an active transaction."""
        pass

    @abstractmethod
    def abort_transaction(self, transaction_id: str) -> TransactionRecord:
        """Abort and rollback an active transaction."""
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        """Retrieve details of a transaction by ID."""
        pass


class IFilesystemProvider(ABC):
    """Interface for Filesystem Subsystem Provider."""

    @abstractmethod
    def get_permission_service(self) -> IPermissionService:
        """Return permission inspection service."""
        pass

    @abstractmethod
    def get_metadata_service(self) -> IMetadataService:
        """Return metadata service."""
        pass

    @abstractmethod
    def get_directory_service(self) -> IDirectoryService:
        """Return directory service."""
        pass

    @abstractmethod
    def get_file_service(self) -> IFileService:
        """Return file service."""
        pass

    @abstractmethod
    def get_search_service(self) -> IFilesystemSearchService:
        """Return search service."""
        pass

    @abstractmethod
    def get_transaction_runtime(self) -> IFilesystemTransactionRuntime:
        """Return transaction runtime."""
        pass

    @abstractmethod
    def get_health(self) -> FilesystemHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> FilesystemStatistics:
        """Return provider statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> FilesystemCapabilities:
        """Return underlying filesystem capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic metrics."""
        pass


class IFilesystemRuntime(ABC):
    """Interface for Filesystem Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize filesystem runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown filesystem runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IFilesystemProvider) -> None:
        """Register filesystem provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IFilesystemProvider]:
        """Get registered filesystem provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> FilesystemStatistics:
        """Get runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> FilesystemRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics dictionary."""
        pass
