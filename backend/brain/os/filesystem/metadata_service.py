"""Metadata Service implementation (Phase 11.2).

Responsible for extracting detailed file and directory metadata, MIME types,
timestamps (created, modified, accessed), hidden status, readonly flag, owner/group,
and symlink detection.
"""

from datetime import datetime, timezone
import mimetypes
import os
from pathlib import Path
import stat
from typing import Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.exceptions import FileNotFoundError, PathSafetyError
from brain.os.filesystem.filesystem_models import DirectoryMetadata, FileMetadata
from brain.os.filesystem.interfaces import IMetadataService, IPermissionService
from brain.os.filesystem.permission_service import PermissionService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class MetadataService(IMetadataService):
    """Provides metadata extraction for files and directories."""

    def __init__(
        self,
        path_service: Optional[IPathService] = None,
        permission_service: Optional[IPermissionService] = None,
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
        self._permission_service = permission_service or PermissionService(
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        mimetypes.init()

    def _resolve_and_validate(self, path: str) -> str:
        if not path:
            raise FileNotFoundError("Path cannot be empty", path=path)

        abs_path = self._path_service.resolve_absolute(path)
        if not self._path_service.is_safe_path(abs_path):
            raise PathSafetyError("Directory traversal detected", path=path)

        return abs_path

    def get_mime_type(self, path: str) -> str:
        """Determine MIME content type of a file."""
        abs_path = self._resolve_and_validate(path)
        mime, _ = mimetypes.guess_type(abs_path)
        return mime or "application/octet-stream"

    def is_hidden(self, path: str) -> bool:
        """Check if file or directory is hidden."""
        abs_path = self._resolve_and_validate(path)
        name = os.path.basename(abs_path) or abs_path
        if name.startswith("."):
            return True

        target_os = self._detector.detect_os()
        if target_os == OperatingSystem.WINDOWS:
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(abs_path)
                if attrs != -1 and (attrs & 2):  # FILE_ATTRIBUTE_HIDDEN = 2
                    return True
            except Exception:
                pass
        return False

    def is_symlink(self, path: str) -> bool:
        """Check if path is a symbolic link."""
        abs_path = self._resolve_and_validate(path)
        return os.path.islink(abs_path)

    def get_file_metadata(self, path: str) -> FileMetadata:
        """Extract detailed metadata for a file."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}", path=path)

        st = os.stat(abs_path)
        name = os.path.basename(abs_path)
        _, ext = os.path.splitext(name)
        mime = self.get_mime_type(abs_path)
        hidden = self.is_hidden(abs_path)
        symlink = self.is_symlink(abs_path)

        symlink_target = None
        if symlink:
            try:
                symlink_target = os.readlink(abs_path)
            except Exception:
                pass

        readonly = not (st.st_mode & stat.S_IWRITE)

        perm_info = self._permission_service.check_permissions(abs_path)

        created_at = datetime.fromtimestamp(st.st_ctime, timezone.utc)
        modified_at = datetime.fromtimestamp(st.st_mtime, timezone.utc)
        accessed_at = datetime.fromtimestamp(st.st_atime, timezone.utc)

        return FileMetadata(
            path=abs_path,
            name=name,
            size_bytes=st.st_size,
            extension=ext,
            mime_type=mime,
            created_at=created_at,
            modified_at=modified_at,
            accessed_at=accessed_at,
            is_hidden=hidden,
            is_readonly=readonly,
            is_symlink=symlink,
            symlink_target=symlink_target,
            owner=perm_info.owner,
            group=perm_info.group,
            permissions_summary=perm_info.permissions_mode,
        )

    def get_directory_metadata(self, path: str) -> DirectoryMetadata:
        """Extract detailed metadata for a directory."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Directory not found: {abs_path}", path=path)

        st = os.stat(abs_path)
        name = os.path.basename(abs_path) or abs_path
        hidden = self.is_hidden(abs_path)
        readonly = not (st.st_mode & stat.S_IWRITE)

        perm_info = self._permission_service.check_permissions(abs_path)

        created_at = datetime.fromtimestamp(st.st_ctime, timezone.utc)
        modified_at = datetime.fromtimestamp(st.st_mtime, timezone.utc)

        child_count = 0
        total_size = 0
        try:
            entries = os.listdir(abs_path)
            child_count = len(entries)
            for entry in entries:
                entry_path = os.path.join(abs_path, entry)
                try:
                    total_size += os.path.getsize(entry_path)
                except Exception:
                    pass
        except Exception:
            pass

        return DirectoryMetadata(
            path=abs_path,
            name=name,
            child_count=child_count,
            total_size_bytes=total_size,
            is_empty=(child_count == 0),
            created_at=created_at,
            modified_at=modified_at,
            is_hidden=hidden,
            is_readonly=readonly,
            permissions_summary=perm_info.permissions_mode,
        )
