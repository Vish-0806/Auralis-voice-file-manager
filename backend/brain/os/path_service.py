"""Path Service implementation (Phase 11.1).

Provides cross-platform path normalization, user directory (~) expansion,
environment variable expansion ($VAR, ${VAR}, %VAR%), absolute path resolution,
directory traversal safety validation, path comparison, canonical path generation,
and path information extraction for Windows, Linux, and macOS.
"""

import os
from pathlib import PurePath, PurePosixPath, PureWindowsPath
import re
from typing import Dict, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem, PathInformation
from brain.os.platform_detector import PlatformDetector


class PathService(IPathService):
    """Handles cross-platform path resolution, normalization, and safety checks."""

    def __init__(
        self,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(platform_detector=self._detector)

    def _determine_target_os(self, target_os: Optional[OperatingSystem] = None) -> OperatingSystem:
        """Helper to resolve target OS or default to detected platform."""
        if target_os is not None and target_os != OperatingSystem.UNKNOWN:
            return target_os
        return self._detector.detect_os()

    def get_separator(self, target_os: Optional[OperatingSystem] = None) -> str:
        """Return directory path separator character for targeted OS."""
        resolved_os = self._determine_target_os(target_os)
        if resolved_os == OperatingSystem.WINDOWS:
            return "\\"
        return "/"

    def normalize_path(self, path: str, target_os: Optional[OperatingSystem] = None) -> str:
        """Normalize slashes, collapse relative components, and strip redundant separators."""
        if not path:
            return ""

        resolved_os = self._determine_target_os(target_os)
        separator = "\\" if resolved_os == OperatingSystem.WINDOWS else "/"

        # Standardize slash direction for processing
        clean_path = path.replace("\\", "/") if resolved_os != OperatingSystem.WINDOWS else path.replace("/", "\\")

        if resolved_os == OperatingSystem.WINDOWS:
            # Handle Windows drive letters and UNC paths
            is_unc = clean_path.startswith("\\\\")
            prefix = ""
            if is_unc:
                prefix = "\\\\"
                clean_path = clean_path[2:]
            elif len(clean_path) >= 2 and clean_path[1] == ":":
                prefix = clean_path[:2]
                clean_path = clean_path[2:]

            parts = [p for p in clean_path.split("\\") if p and p != "."]
            stack = []
            for part in parts:
                if part == "..":
                    if stack:
                        stack.pop()
                else:
                    stack.append(part)

            joined = "\\".join(stack)
            if prefix:
                if prefix.endswith(":") and not joined:
                    return prefix + "\\"
                return f"{prefix}\\{joined}" if joined else prefix
            elif path.startswith("\\"):
                return f"\\{joined}" if joined else "\\"
            return joined
        else:
            is_absolute = clean_path.startswith("/")
            parts = [p for p in clean_path.split("/") if p and p != "."]
            stack = []
            for part in parts:
                if part == "..":
                    if stack:
                        stack.pop()
                else:
                    stack.append(part)

            joined = "/".join(stack)
            if is_absolute:
                return f"/{joined}"
            return joined

    def expand_user(self, path: str, home_override: Optional[str] = None) -> str:
        """Expand user home directory tilde (~) notation."""
        if not path:
            return ""

        home = home_override or self._env_service.get_home_directory()

        if path == "~":
            return home
        elif path.startswith("~/") or path.startswith("~\\"):
            return os.path.join(home, path[2:])
        elif path.startswith("~"):
            # ~username syntax handling
            idx = max(path.find("/"), path.find("\\"))
            if idx == -1:
                return home
            return os.path.join(home, path[idx + 1:])

        return path

    def expand_vars(self, path: str, env_override: Optional[Dict[str, str]] = None) -> str:
        """Expand $VAR, ${VAR}, and %VAR% environment variables."""
        if not path:
            return ""

        env_map = self._env_service.get_environment_variables()
        if env_override:
            env_map.update(env_override)

        # 1. Expand %VAR% (Windows style)
        def replace_win_var(match: re.Match) -> str:
            var_name = match.group(1)
            return env_map.get(var_name, match.group(0))

        result = re.sub(r"%([^%]+)%", replace_win_var, path)

        # 2. Expand ${VAR} and $VAR (Unix style)
        def replace_unix_var(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            return env_map.get(var_name, match.group(0))

        result = re.sub(r"\$\{([A-Za-z0-9_]+)\}|\$([A-Za-z0-9_]+)", replace_unix_var, result)
        return result

    def resolve_absolute(self, path: str, base_dir: Optional[str] = None) -> str:
        """Resolve path to an absolute path against base_dir or CWD."""
        if not path:
            base = base_dir or self._env_service.get_cwd()
            return self.normalize_path(base)

        expanded = self.expand_user(path)
        expanded = self.expand_vars(expanded)

        resolved_os = self._detector.detect_os()

        # Check if expanded path is already absolute
        is_abs = False
        if resolved_os == OperatingSystem.WINDOWS:
            is_abs = bool(re.match(r"^[a-zA-Z]:[\\/]", expanded)) or expanded.startswith("\\\\") or expanded.startswith("/") or expanded.startswith("\\")
        else:
            is_abs = expanded.startswith("/")

        if is_abs:
            if resolved_os == OperatingSystem.WINDOWS and (expanded.startswith("/") or expanded.startswith("\\")) and not (expanded.startswith("\\\\") or re.match(r"^[a-zA-Z]:[\\/]", expanded)):
                base = base_dir or self._env_service.get_cwd()
                drive = "C:"
                if len(base) >= 2 and base[1] == ":":
                    drive = base[:2]
                expanded = f"{drive}{expanded}"
            return self.normalize_path(expanded, target_os=resolved_os)

        base = base_dir or self._env_service.get_cwd()
        sep = self.get_separator(target_os=resolved_os)
        combined = f"{base}{sep}{expanded}"
        return self.normalize_path(combined, target_os=resolved_os)

    def is_safe_path(self, path: str, base_dir: Optional[str] = None) -> bool:
        """Validate whether path stays within base_dir without directory traversal."""
        if not path:
            return True

        base = base_dir or self._env_service.get_cwd()
        abs_base = self.resolve_absolute(base)
        abs_target = self.resolve_absolute(path, base_dir=abs_base)

        target_os = self._detector.detect_os()
        if target_os in (OperatingSystem.WINDOWS, OperatingSystem.MACOS):
            norm_base = abs_base.lower()
            norm_target = abs_target.lower()
        else:
            norm_base = abs_base
            norm_target = abs_target

        sep = self.get_separator(target_os=target_os)
        if not norm_base.endswith(sep):
            norm_base_with_sep = norm_base + sep
        else:
            norm_base_with_sep = norm_base

        return norm_target == norm_base or norm_target.startswith(norm_base_with_sep)

    def compare_paths(
        self, path1: str, path2: str, target_os: Optional[OperatingSystem] = None
    ) -> bool:
        """Compare two paths for logical equality considering target OS case sensitivity."""
        resolved_os = self._determine_target_os(target_os)
        norm1 = self.normalize_path(path1, target_os=resolved_os)
        norm2 = self.normalize_path(path2, target_os=resolved_os)

        if resolved_os in (OperatingSystem.WINDOWS, OperatingSystem.MACOS):
            return norm1.lower() == norm2.lower()
        return norm1 == norm2

    def get_canonical_path(self, path: str) -> str:
        """Return fully canonicalized absolute path."""
        abs_path = self.resolve_absolute(path)
        try:
            return os.path.realpath(abs_path)
        except Exception:
            return abs_path

    def get_path_info(self, path: str) -> PathInformation:
        """Return detailed PathInformation model for a given path."""
        target_os = self._detector.detect_os()
        sep = self.get_separator(target_os=target_os)

        canonical = self.get_canonical_path(path)
        norm = self.normalize_path(path, target_os=target_os)
        abs_path = self.resolve_absolute(path)

        is_abs = False
        if target_os == OperatingSystem.WINDOWS:
            is_abs = bool(re.match(r"^[a-zA-Z]:[\\/]", abs_path)) or abs_path.startswith("\\\\")
        else:
            is_abs = abs_path.startswith("/")

        is_safe = self.is_safe_path(path)
        exists = os.path.exists(abs_path)
        is_file = os.path.isfile(abs_path)
        is_dir = os.path.isdir(abs_path)

        _, ext = os.path.splitext(abs_path)
        parent = os.path.dirname(abs_path)

        return PathInformation(
            original_path=path,
            normalized_path=norm,
            absolute_path=abs_path,
            is_absolute=is_abs,
            is_safe=is_safe,
            exists=exists,
            is_file=is_file,
            is_directory=is_dir,
            extension=ext,
            parent_path=parent,
            path_separator=sep,
        )
