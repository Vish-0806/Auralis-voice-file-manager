"""Filesystem Subsystem for Auralis Operating System Abstraction (Phase 11.2).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.filesystem.directory_service import DirectoryService
from brain.os.filesystem.exceptions import (
    DirectoryNotEmptyError,
    FileExistsError,
    FileNotFoundError,
    FilesystemException,
    PathSafetyError,
    PermissionDeniedError,
    TransactionError,
)
from brain.os.filesystem.file_service import FileService
from brain.os.filesystem.filesystem_models import (
    DirectoryMetadata,
    FileMetadata,
    FilesystemCapabilities,
    FilesystemEntry,
    FilesystemEntryType,
    FilesystemHealth,
    FilesystemRuntimeStatus,
    FilesystemStatistics,
    OperationResult,
    OperationStatus,
    PermissionInfo,
    PermissionType,
    SearchResult,
    TransactionRecord,
)
from brain.os.filesystem.filesystem_provider import FilesystemProvider
from brain.os.filesystem.filesystem_runtime import FilesystemRuntime
from brain.os.filesystem.interfaces import (
    IDirectoryService,
    IFileService,
    IFilesystemProvider,
    IFilesystemRuntime,
    IFilesystemSearchService,
    IFilesystemTransactionRuntime,
    IMetadataService,
    IPermissionService,
)
from brain.os.filesystem.metadata_service import MetadataService
from brain.os.filesystem.permission_service import PermissionService
from brain.os.filesystem.runtime import get_filesystem_runtime, reset_filesystem_runtime
from brain.os.filesystem.search_service import FilesystemSearchService
from brain.os.filesystem.transaction_runtime import FilesystemTransactionRuntime

__all__ = [
    # Enums
    "FilesystemEntryType",
    "PermissionType",
    "OperationStatus",
    # Models
    "FilesystemEntry",
    "FileMetadata",
    "DirectoryMetadata",
    "PermissionInfo",
    "FilesystemStatistics",
    "SearchResult",
    "TransactionRecord",
    "FilesystemHealth",
    "FilesystemRuntimeStatus",
    "OperationResult",
    "FilesystemCapabilities",
    # Exceptions
    "FilesystemException",
    "PermissionDeniedError",
    "FileNotFoundError",
    "FileExistsError",
    "DirectoryNotEmptyError",
    "TransactionError",
    "PathSafetyError",
    # Interfaces
    "IPermissionService",
    "IMetadataService",
    "IDirectoryService",
    "IFileService",
    "IFilesystemSearchService",
    "IFilesystemTransactionRuntime",
    "IFilesystemProvider",
    "IFilesystemRuntime",
    # Services & Implementations
    "PermissionService",
    "MetadataService",
    "DirectoryService",
    "FileService",
    "FilesystemSearchService",
    "FilesystemTransactionRuntime",
    "FilesystemProvider",
    "FilesystemRuntime",
    # Singleton Accessors
    "get_filesystem_runtime",
    "reset_filesystem_runtime",
]
