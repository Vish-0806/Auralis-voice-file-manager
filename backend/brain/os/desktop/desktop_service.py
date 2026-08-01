"""Desktop Service implementation (Phase 11.5).

Provides platform-independent discovery of standard system known folders (Desktop, Documents,
Downloads, Pictures, Videos, Music, Home, Temp) and desktop environment metadata across
Windows, Linux, and macOS.
"""

import os
import tempfile
from typing import Dict, Optional

from brain.os.desktop.desktop_models import (
    DesktopEnvironment,
    DesktopInfo,
    KnownFolder,
    KnownFolderType,
)
from brain.os.desktop.interfaces import IDesktopService
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class DesktopService(IDesktopService):
    """Platform-independent desktop environment service."""

    def __init__(
        self,
        environment_service: Optional[IEnvironmentService] = None,
        path_service: Optional[IPathService] = None,
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

    def _resolve_folder_path(self, folder_type: KnownFolderType, home_dir: str) -> str:
        """Resolve expected folder path based on folder type and platform."""
        target_os = self._detector.detect_os()

        if folder_type == KnownFolderType.HOME:
            return home_dir
        elif folder_type == KnownFolderType.TEMP:
            return tempfile.gettempdir()

        folder_name_map = {
            KnownFolderType.DESKTOP: "Desktop",
            KnownFolderType.DOCUMENTS: "Documents",
            KnownFolderType.DOWNLOADS: "Downloads",
            KnownFolderType.PICTURES: "Pictures",
            KnownFolderType.VIDEOS: "Videos" if target_os != OperatingSystem.WINDOWS else "Videos",
            KnownFolderType.MUSIC: "Music",
        }

        sub = folder_name_map.get(folder_type, "")
        if sub:
            return os.path.join(home_dir, sub)
        return home_dir

    def get_known_folders(self) -> Dict[KnownFolderType, KnownFolder]:
        """Discover all standard system known folders."""
        home_dir = self._path_service.expand_user("~")
        results: Dict[KnownFolderType, KnownFolder] = {}

        for ktype in KnownFolderType:
            path = self._resolve_folder_path(ktype, home_dir)
            exists = os.path.exists(path)
            writable = os.access(path, os.W_OK) if exists else False

            results[ktype] = KnownFolder(
                folder_type=ktype,
                name=ktype.value.capitalize(),
                path=path,
                exists=exists,
                is_writable=writable,
            )

        return results

    def get_known_folder(self, folder_type: KnownFolderType) -> Optional[KnownFolder]:
        """Get details for a specific known folder type."""
        folders = self.get_known_folders()
        return folders.get(folder_type)

    def get_desktop_info(self) -> DesktopInfo:
        """Get desktop environment session details and known folders map."""
        target_os = self._detector.detect_os()

        env = DesktopEnvironment.UNKNOWN
        if target_os == OperatingSystem.WINDOWS:
            env = DesktopEnvironment.WINDOWS
        elif target_os == OperatingSystem.MACOS:
            env = DesktopEnvironment.MACOS
        else:
            desktop_env_var = (
                self._env_service.get_env_var("XDG_CURRENT_DESKTOP") or ""
            ).lower()
            if "gnome" in desktop_env_var:
                env = DesktopEnvironment.GNOME
            elif "kde" in desktop_env_var:
                env = DesktopEnvironment.KDE
            elif "xfce" in desktop_env_var:
                env = DesktopEnvironment.XFCE

        user_name = self._env_service.get_username()
        session_id = (
            self._env_service.get_env_var("SESSIONNAME")
            or self._env_service.get_env_var("XDG_SESSION_ID")
            or "console"
        )

        folders = self.get_known_folders()
        str_folders = {k.value: v for k, v in folders.items()}

        return DesktopInfo(
            environment=env,
            display_name=f"{target_os.value.capitalize()} Desktop",
            session_id=session_id,
            user_name=user_name,
            known_folders=str_folders,
        )
