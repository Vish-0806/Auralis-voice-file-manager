"""File Service implementation (Phase 11.2).

Provides safe text and byte reading/writing, atomic writes via temp file swap,
copy, move, rename, delete, and overwrite policy enforcement.
"""

import os
import shutil
import tempfile
import time
from typing import Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.exceptions import (
    FileExistsError,
    FileNotFoundError,
    PermissionDeniedError,
    PathSafetyError,
)
from brain.os.filesystem.filesystem_models import OperationResult, OperationStatus
from brain.os.filesystem.interfaces import IFileService, IPermissionService
from brain.os.filesystem.permission_service import PermissionService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class FileService(IFileService):
    """Provides safe file I/O operations and manipulation methods."""

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

    def _resolve_and_validate(self, path: str) -> str:
        if not path:
            raise FileNotFoundError("Path cannot be empty", path=path)

        abs_path = self._path_service.resolve_absolute(path)
        if not self._path_service.is_safe_path(abs_path):
            raise PathSafetyError("Directory traversal detected", path=path)

        return abs_path

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}", path=path)
        if not self._permission_service.can_read(abs_path):
            raise PermissionDeniedError(f"Permission denied reading: {abs_path}", path=path)

        with open(abs_path, "r", encoding=encoding) as f:
            return f.read()

    def read_bytes(self, path: str) -> bytes:
        """Read raw bytes from a file."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}", path=path)
        if not self._permission_service.can_read(abs_path):
            raise PermissionDeniedError(f"Permission denied reading: {abs_path}", path=path)

        with open(abs_path, "rb") as f:
            return f.read()

    def write_bytes(
        self,
        path: str,
        data: bytes,
        atomic: bool = True,
        overwrite: bool = True,
    ) -> OperationResult:
        """Write bytes to file with optional atomic swap and overwrite policy."""
        start_t = time.time()
        abs_path = self._resolve_and_validate(path)

        if os.path.exists(abs_path) and not overwrite:
            raise FileExistsError(f"File already exists and overwrite=False: {abs_path}", path=path)

        parent_dir = os.path.dirname(abs_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        if atomic:
            temp_fd, temp_path = tempfile.mkstemp(dir=parent_dir)
            try:
                with os.fdopen(temp_fd, "wb") as f:
                    f.write(data)
                shutil.move(temp_path, abs_path)
            except Exception as e:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                duration = (time.time() - start_t) * 1000.0
                return OperationResult(
                    status=OperationStatus.FAILED,
                    operation_type="write_bytes",
                    source_path=abs_path,
                    bytes_affected=0,
                    duration_ms=duration,
                    error=str(e),
                )
        else:
            with open(abs_path, "wb") as f:
                f.write(data)

        duration = (time.time() - start_t) * 1000.0
        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type="write_bytes",
            source_path=abs_path,
            bytes_affected=len(data),
            duration_ms=duration,
        )

    def write_text(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = True,
        overwrite: bool = True,
    ) -> OperationResult:
        """Write text to file with optional atomic swap and overwrite policy."""
        data = content.encode(encoding)
        res = self.write_bytes(path, data, atomic=atomic, overwrite=overwrite)
        return OperationResult(
            status=res.status,
            operation_type="write_text",
            source_path=res.source_path,
            bytes_affected=res.bytes_affected,
            duration_ms=res.duration_ms,
            error=res.error,
        )

    def copy_file(
        self, source: str, destination: str, overwrite: bool = True
    ) -> OperationResult:
        """Copy file from source to destination."""
        start_t = time.time()
        abs_src = self._resolve_and_validate(source)
        abs_dst = self._resolve_and_validate(destination)

        if not os.path.exists(abs_src):
            raise FileNotFoundError(f"Source file not found: {abs_src}", path=source)
        if os.path.exists(abs_dst) and not overwrite:
            raise FileExistsError(f"Destination exists and overwrite=False: {abs_dst}", path=destination)

        dst_dir = os.path.dirname(abs_dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)

        size = os.path.getsize(abs_src)
        shutil.copy2(abs_src, abs_dst)

        duration = (time.time() - start_t) * 1000.0
        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type="copy_file",
            source_path=abs_src,
            target_path=abs_dst,
            bytes_affected=size,
            duration_ms=duration,
        )

    def move_file(
        self, source: str, destination: str, overwrite: bool = True
    ) -> OperationResult:
        """Move file from source to destination."""
        start_t = time.time()
        abs_src = self._resolve_and_validate(source)
        abs_dst = self._resolve_and_validate(destination)

        if not os.path.exists(abs_src):
            raise FileNotFoundError(f"Source file not found: {abs_src}", path=source)
        if os.path.exists(abs_dst) and not overwrite:
            raise FileExistsError(f"Destination exists and overwrite=False: {abs_dst}", path=destination)

        dst_dir = os.path.dirname(abs_dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)

        size = os.path.getsize(abs_src)
        if os.path.exists(abs_dst) and overwrite:
            if os.path.isdir(abs_dst):
                shutil.rmtree(abs_dst)
            else:
                os.remove(abs_dst)

        shutil.move(abs_src, abs_dst)

        duration = (time.time() - start_t) * 1000.0
        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type="move_file",
            source_path=abs_src,
            target_path=abs_dst,
            bytes_affected=size,
            duration_ms=duration,
        )

    def rename_file(self, path: str, new_name: str) -> OperationResult:
        """Rename a file or directory in place."""
        abs_path = self._resolve_and_validate(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path not found: {abs_path}", path=path)

        parent = os.path.dirname(abs_path)
        new_path = os.path.join(parent, new_name)
        return self.move_file(abs_path, new_path, overwrite=False)

    def delete_file(self, path: str) -> OperationResult:
        """Delete a file or directory."""
        start_t = time.time()
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path not found: {abs_path}", path=path)

        size = 0
        if os.path.isfile(abs_path) or os.path.islink(abs_path):
            size = os.path.getsize(abs_path)
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)

        duration = (time.time() - start_t) * 1000.0
        return OperationResult(
            status=OperationStatus.SUCCESS,
            operation_type="delete_file",
            source_path=abs_path,
            bytes_affected=size,
            duration_ms=duration,
        )
