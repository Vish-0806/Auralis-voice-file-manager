"""Launcher Service implementation (Phase 11.3).

Provides safe, platform-independent application execution via subprocess.Popen.
Supports launching by executable, application name, or alias, handling custom arguments,
working directory, environment variables, launch modes, and pre-execution validation.
"""

import os
import subprocess
import time
from typing import List, Optional

from brain.os.application.application_detector import ApplicationDetector
from brain.os.application.application_models import (
    ApplicationLaunchRequest,
    ApplicationLaunchResult,
    LaunchMode,
)
from brain.os.application.application_registry import ApplicationRegistry
from brain.os.application.exceptions import (
    ApplicationLaunchError,
    ApplicationNotFoundError,
)
from brain.os.application.interfaces import (
    IApplicationDetector,
    IApplicationRegistry,
    ILauncherService,
)
from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class LauncherService(ILauncherService):
    """Provides application launch execution and management."""

    def __init__(
        self,
        registry: Optional[IApplicationRegistry] = None,
        detector: Optional[IApplicationDetector] = None,
        path_service: Optional[IPathService] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector_component = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector_component
        )
        self._path_service = path_service or PathService(
            environment_service=self._env_service,
            platform_detector=self._detector_component,
        )
        self._registry = registry or ApplicationRegistry()
        self._detector = detector or ApplicationDetector(
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector_component,
        )

    def launch_executable(
        self,
        executable_path: str,
        arguments: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
    ) -> ApplicationLaunchResult:
        """Directly launch an executable file with arguments."""
        req = ApplicationLaunchRequest(
            app_id_or_name=executable_path,
            arguments=arguments or [],
            working_directory=working_dir,
        )
        return self.launch(req)

    def launch(self, request: ApplicationLaunchRequest) -> ApplicationLaunchResult:
        """Launch an application given a launch specification request."""
        start_t = time.time()
        target = request.app_id_or_name

        if not target:
            raise ApplicationNotFoundError("Application target cannot be empty")

        # 1. Resolve executable path
        exec_path: Optional[str] = None

        # Check registry first
        reg_app = self._registry.get_application(target) or self._registry.get_by_alias(target)
        if reg_app and reg_app.info.executable_path:
            exec_path = reg_app.info.executable_path

        # Check detector fallback
        if not exec_path:
            exec_path = self._detector.find_executable(target)

        if not exec_path or not os.path.exists(exec_path):
            raise ApplicationNotFoundError(f"Application not found or executable invalid: '{target}'", app_id=target)

        # 2. Prepare environment and working directory
        env = self._env_service.get_environment_variables()
        if request.env_vars:
            env.update(request.env_vars)

        cwd = request.working_directory
        if cwd:
            cwd = self._path_service.resolve_absolute(cwd)
            if not os.path.exists(cwd):
                cwd = None

        cmd = [exec_path] + list(request.arguments)

        # 3. Configure platform-specific startup flags for LaunchMode
        creation_flags = 0
        target_os = self._detector_component.detect_os()

        if target_os == OperatingSystem.WINDOWS:
            if request.launch_mode == LaunchMode.BACKGROUND:
                # CREATE_NO_WINDOW = 0x08000000
                creation_flags |= 0x08000000

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                creationflags=creation_flags if target_os == OperatingSystem.WINDOWS else 0,
            )
            duration = (time.time() - start_t) * 1000.0

            app_id = reg_app.info.app_id if reg_app else os.path.basename(exec_path)

            return ApplicationLaunchResult(
                success=True,
                process_id=proc.pid,
                app_id=app_id,
                executable_path=exec_path,
                launch_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start_t) * 1000.0
            raise ApplicationLaunchError(f"Failed to launch application '{target}': {e}", app_id=target)
