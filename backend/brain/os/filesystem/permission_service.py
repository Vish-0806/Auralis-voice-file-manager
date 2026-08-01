"""Permission Service implementation (Phase 11.2).

Provides read-only inspection of read, write, execute, and delete access permissions,
as well as owner/group information across Windows, Linux, and macOS platforms.
Integrates with Phase 11.1 PathService for safety checks.
"""

import getpass
import os
import stat
from typing import Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.exceptions import FileNotFoundError, PathSafetyError
from brain.os.filesystem.filesystem_models import PermissionInfo
from brain.os.filesystem.interfaces import IPermissionService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class PermissionService(IPermissionService):
    """Read-only permission inspection service."""

    def __init__(
        self,
        path_service: Optional[IPathService] = None,
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

    def _resolve_and_validate(self, path: str) -> str:
        """Helper to resolve, normalize, and validate path safety."""
        if not path:
            raise FileNotFoundError("Path cannot be empty", path=path)

        abs_path = self._path_service.resolve_absolute(path)
        if not self._path_service.is_safe_path(abs_path):
            raise PathSafetyError("Directory traversal detected", path=path)

        return abs_path

    def check_permissions(self, path: str) -> PermissionInfo:
        """Inspect and return permission info for a path."""
        abs_path = self._resolve_and_validate(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path not found: {abs_path}", path=path)

        can_r = os.access(abs_path, os.R_OK)
        can_w = os.access(abs_path, os.W_OK)
        can_x = os.access(abs_path, os.X_OK)

        # Delete check: requires write permission on parent directory
        parent = os.path.dirname(abs_path) or abs_path
        can_d = os.access(parent, os.W_OK) if os.path.exists(parent) else False

        owner = ""
        group = ""
        mode_str = ""

        try:
            st = os.stat(abs_path)
            mode_str = oct(stat.S_IMODE(st.st_mode))

            target_os = self._detector.detect_os()
            if target_os != OperatingSystem.WINDOWS:
                try:
                    import pwd
                    import grp
                    owner = pwd.getpwuid(st.st_uid).pw_name
                    group = grp.getgrgid(st.st_gid).gr_name
                except Exception:
                    owner = str(st.st_uid)
                    group = str(st.st_gid)
            else:
                owner = self._env_service.get_username()
                group = "Users"
        except Exception:
            owner = self._env_service.get_username()
            group = "Users"

        return PermissionInfo(
            path=abs_path,
            can_read=can_r,
            can_write=can_w,
            can_execute=can_x,
            can_delete=can_d,
            owner=owner,
            group=group,
            permissions_mode=mode_str,
        )

    def can_read(self, path: str) -> bool:
        """Check if path is readable."""
        try:
            info = self.check_permissions(path)
            return info.can_read
        except Exception:
            return False

    def can_write(self, path: str) -> bool:
        """Check if path is writable."""
        try:
            info = self.check_permissions(path)
            return info.can_write
        except Exception:
            return False

    def can_execute(self, path: str) -> bool:
        """Check if path is executable."""
        try:
            info = self.check_permissions(path)
            return info.can_execute
        except Exception:
            return False

    def can_delete(self, path: str) -> bool:
        """Check if path can be deleted."""
        try:
            info = self.check_permissions(path)
            return info.can_delete
        except Exception:
            return False
