"""Application Detector implementation (Phase 11.3).

Provides platform-independent desktop application discovery and executable path resolution
using system PATH, environment variables, and standard installation directories across
Windows, Linux, and macOS.
"""

import os
import shutil
from typing import List, Optional

from brain.os.application.application_models import ApplicationInfo, InstalledApplication
from brain.os.application.interfaces import IApplicationDetector
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class ApplicationDetector(IApplicationDetector):
    """Platform-independent desktop application detector."""

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

    def find_executable(self, name_or_alias: str) -> Optional[str]:
        """Resolve executable path for an application name or alias."""
        if not name_or_alias:
            return None

        # 1. Direct path check
        if os.path.isabs(name_or_alias) and os.path.isfile(name_or_alias):
            return name_or_alias

        # 2. System PATH lookup via shutil.which
        resolved = shutil.which(name_or_alias)
        if resolved:
            return resolved

        # Append platform extension if missing (e.g. .exe on Windows)
        target_os = self._detector.detect_os()
        if target_os == OperatingSystem.WINDOWS and not name_or_alias.lower().endswith(".exe"):
            resolved = shutil.which(f"{name_or_alias}.exe")
            if resolved:
                return resolved

        # 3. Check common install directories
        common_dirs: List[str] = []
        if target_os == OperatingSystem.WINDOWS:
            pf = self._env_service.get_env_var("ProgramFiles") or "C:\\Program Files"
            pfx86 = self._env_service.get_env_var("ProgramFiles(x86)") or "C:\\Program Files (x86)"
            local_app = self._env_service.get_env_var("LOCALAPPDATA") or ""
            common_dirs.extend([pf, pfx86, local_app])
        elif target_os == OperatingSystem.MACOS:
            common_dirs.extend(["/Applications", "/System/Applications", "~/Applications"])
        else:
            common_dirs.extend(["/usr/bin", "/usr/local/bin", "/opt", "~/.local/bin"])

        base_name = name_or_alias.lower()
        for cdir in common_dirs:
            if not cdir:
                continue
            expanded_dir = self._path_service.expand_user(cdir)
            if not os.path.exists(expanded_dir):
                continue

            try:
                for root, _, files in os.walk(expanded_dir):
                    for file in files:
                        f_lower = file.lower()
                        if f_lower == base_name or f_lower == f"{base_name}.exe":
                            full_path = os.path.join(root, file)
                            if os.access(full_path, os.X_OK):
                                return full_path
                    # Limit depth to prevent long walk
                    if root.count(os.sep) - expanded_dir.count(os.sep) >= 2:
                        break
            except Exception:
                pass

        return None

    def is_installed(self, name_or_alias: str) -> bool:
        """Check if an application is installed on the host OS."""
        return self.find_executable(name_or_alias) is not None

    def detect_installed_applications(self) -> List[InstalledApplication]:
        """Discover installed desktop applications on the host platform."""
        results: List[InstalledApplication] = []

        # Common standard tools to discover
        known_apps = [
            ("notepad", "Notepad", "Text Editor", ["txt", "editor"]),
            ("calc", "Calculator", "Utility", ["calculator"]),
            ("cmd", "Command Prompt", "System", ["cli", "terminal"]),
            ("powershell", "PowerShell", "System", ["ps"]),
            ("explorer", "File Explorer", "System", ["files"]),
            ("bash", "Bash", "System", ["shell", "terminal"]),
            ("python", "Python Interpreter", "Development", ["py"]),
        ]

        for exe_name, name, category, aliases in known_apps:
            exec_path = self.find_executable(exe_name)
            if exec_path:
                app_id = name.lower().replace(" ", "_")
                info = ApplicationInfo(
                    app_id=app_id,
                    name=name,
                    display_name=name,
                    executable_path=exec_path,
                    category=category,
                    aliases=aliases,
                )
                app = InstalledApplication(
                    info=info,
                    install_path=os.path.dirname(exec_path),
                    is_system_app=True,
                    categories=[category],
                )
                results.append(app)

        return results
