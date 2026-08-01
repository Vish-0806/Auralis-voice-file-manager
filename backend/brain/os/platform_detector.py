"""Platform Detector implementation (Phase 11.1).

Responsible for detecting operating system family, hardware architecture,
hostname, Python version, processor, machine type, release, and version details.
Supports constructor injection for isolated testing.
"""

import platform
import socket
import struct
import sys
from typing import Optional

from brain.os.interfaces import IPlatformDetector
from brain.os.os_models import (
    Architecture,
    OperatingSystem,
    OperatingSystemInfo,
    PlatformArchitecture,
)


class PlatformDetector(IPlatformDetector):
    """Detects system hardware and OS characteristics without mutable state."""

    def __init__(
        self,
        os_override: Optional[OperatingSystem] = None,
        arch_override: Optional[Architecture] = None,
        hostname_override: Optional[str] = None,
        python_version_override: Optional[str] = None,
    ) -> None:
        self._os_override = os_override
        self._arch_override = arch_override
        self._hostname_override = hostname_override
        self._python_version_override = python_version_override

    def detect_os(self) -> OperatingSystem:
        """Detect operating system family."""
        if self._os_override is not None:
            return self._os_override

        sys_plat = sys.platform.lower()
        if sys_plat.startswith("win"):
            return OperatingSystem.WINDOWS
        elif sys_plat.startswith("linux"):
            return OperatingSystem.LINUX
        elif sys_plat == "darwin":
            return OperatingSystem.MACOS

        plat_sys = platform.system().lower()
        if "windows" in plat_sys:
            return OperatingSystem.WINDOWS
        elif "linux" in plat_sys:
            return OperatingSystem.LINUX
        elif "darwin" in plat_sys:
            return OperatingSystem.MACOS

        return OperatingSystem.UNKNOWN

    def detect_architecture(self) -> Architecture:
        """Detect hardware CPU architecture."""
        if self._arch_override is not None:
            return self._arch_override

        machine = platform.machine().lower()
        if machine in ("amd64", "x86_64", "x64"):
            return Architecture.X64
        elif machine in ("i386", "i686", "x86"):
            return Architecture.X86
        elif machine in ("aarch64", "arm64"):
            return Architecture.ARM64
        elif "arm" in machine:
            return Architecture.ARM

        # Fallback check via struct pointer size
        bits, _ = platform.architecture()
        if bits == "64bit":
            return Architecture.X64
        elif bits == "32bit":
            return Architecture.X86

        return Architecture.UNKNOWN

    def detect_system_info(self) -> OperatingSystemInfo:
        """Gather comprehensive system identification metadata into immutable model."""
        os_family = self.detect_os()
        arch = self.detect_architecture()
        
        hostname = self._hostname_override
        if hostname is None:
            try:
                hostname = socket.gethostname()
            except Exception:
                hostname = platform.node() or ""

        py_ver = self._python_version_override or platform.python_version()
        processor = platform.processor() or ""
        machine = platform.machine() or ""
        release = platform.release() or ""
        plat_ver = platform.version() or ""

        return OperatingSystemInfo(
            operating_system=os_family,
            architecture=arch,
            hostname=hostname,
            python_version=py_ver,
            processor=processor,
            machine=machine,
            platform_release=release,
            platform_version=plat_ver,
        )

    def detect_platform_architecture(self) -> PlatformArchitecture:
        """Gather detailed platform architecture metadata into immutable model."""
        arch = self.detect_architecture()
        pointer_bitness = struct.calcsize("P") * 8
        is_64bit = pointer_bitness == 64
        endianness = sys.byteorder

        return PlatformArchitecture(
            architecture=arch,
            pointer_bitness=pointer_bitness,
            is_64bit=is_64bit,
            endianness=endianness,
        )
