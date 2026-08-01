"""Environment Service implementation (Phase 11.1).

Provides inspection of runtime process environment details including home directory,
current working directory, temporary directory, environment variables, user account,
timezone, locale, Python binary path, and process ID.
"""

import getpass
import locale
import os
from pathlib import Path
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from brain.os.interfaces import IEnvironmentService, IPlatformDetector
from brain.os.os_models import EnvironmentSnapshot
from brain.os.platform_detector import PlatformDetector


class EnvironmentService(IEnvironmentService):
    """Provides safe access to system environment and runtime context."""

    def __init__(
        self,
        platform_detector: Optional[IPlatformDetector] = None,
        env_overrides: Optional[Dict[str, str]] = None,
        home_override: Optional[str] = None,
        cwd_override: Optional[str] = None,
        temp_dir_override: Optional[str] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_overrides = dict(env_overrides or {})
        self._home_override = home_override
        self._cwd_override = cwd_override
        self._temp_dir_override = temp_dir_override

    def get_home_directory(self) -> str:
        """Return user home directory path."""
        if self._home_override:
            return self._home_override
        try:
            return str(Path.home())
        except Exception:
            return os.path.expanduser("~")

    def get_cwd(self) -> str:
        """Return current working directory path."""
        if self._cwd_override:
            return self._cwd_override
        try:
            return os.getcwd()
        except Exception:
            return "."

    def get_temp_directory(self) -> str:
        """Return temporary files directory path."""
        if self._temp_dir_override:
            return self._temp_dir_override
        return tempfile.gettempdir()

    def get_environment_variables(self) -> Dict[str, str]:
        """Return copy of active environment variables combined with overrides."""
        vars_copy = dict(os.environ)
        vars_copy.update(self._env_overrides)
        return vars_copy

    def get_env_var(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Lookup specific environment variable."""
        if name in self._env_overrides:
            return self._env_overrides[name]
        return os.environ.get(name, default)

    def get_username(self) -> str:
        """Return current user account name."""
        try:
            return getpass.getuser()
        except Exception:
            return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    def get_timezone(self) -> str:
        """Return system timezone string."""
        try:
            return time.tzname[0] if time.tzname else "UTC"
        except Exception:
            return "UTC"

    def get_locale(self) -> str:
        """Return current system locale string."""
        try:
            loc = locale.getlocale()
            if loc and loc[0]:
                return f"{loc[0]}.{loc[1]}" if loc[1] else loc[0]
            loc_default = locale.getdefaultlocale()
            if loc_default and loc_default[0]:
                return f"{loc_default[0]}.{loc_default[1]}" if loc_default[1] else loc_default[0]
        except Exception:
            pass
        return "en_US.UTF-8"

    def get_python_executable(self) -> str:
        """Return absolute path to active Python binary."""
        return sys.executable or ""

    def get_process_id(self) -> int:
        """Return current process ID."""
        return os.getpid()

    def capture_snapshot(self) -> EnvironmentSnapshot:
        """Capture an immutable snapshot of current environment state."""
        return EnvironmentSnapshot(
            home_directory=self.get_home_directory(),
            current_working_directory=self.get_cwd(),
            temp_directory=self.get_temp_directory(),
            environment_variables=self.get_environment_variables(),
            username=self.get_username(),
            timezone=self.get_timezone(),
            locale=self.get_locale(),
            python_executable=self.get_python_executable(),
            process_id=self.get_process_id(),
            captured_at=datetime.now(timezone.utc),
        )
