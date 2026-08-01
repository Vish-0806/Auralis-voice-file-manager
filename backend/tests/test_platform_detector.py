"""Unit tests for PlatformDetector (Phase 11.1)."""

from brain.os import (
    Architecture,
    OperatingSystem,
    OperatingSystemInfo,
    PlatformArchitecture,
    PlatformDetector,
)


def test_platform_detector_defaults() -> None:
    detector = PlatformDetector()
    os_detected = detector.detect_os()
    assert isinstance(os_detected, OperatingSystem)

    arch_detected = detector.detect_architecture()
    assert isinstance(arch_detected, Architecture)

    sys_info = detector.detect_system_info()
    assert isinstance(sys_info, OperatingSystemInfo)
    assert sys_info.operating_system == os_detected
    assert sys_info.architecture == arch_detected
    assert isinstance(sys_info.hostname, str)
    assert isinstance(sys_info.python_version, str)

    plat_arch = detector.detect_platform_architecture()
    assert isinstance(plat_arch, PlatformArchitecture)
    assert plat_arch.pointer_bitness in (32, 64)
    assert isinstance(plat_arch.is_64bit, bool)
    assert plat_arch.endianness in ("little", "big")


def test_platform_detector_overrides() -> None:
    detector = PlatformDetector(
        os_override=OperatingSystem.LINUX,
        arch_override=Architecture.ARM64,
        hostname_override="custom-box",
        python_version_override="3.11.0",
    )

    assert detector.detect_os() == OperatingSystem.LINUX
    assert detector.detect_architecture() == Architecture.ARM64

    sys_info = detector.detect_system_info()
    assert sys_info.operating_system == OperatingSystem.LINUX
    assert sys_info.architecture == Architecture.ARM64
    assert sys_info.hostname == "custom-box"
    assert sys_info.python_version == "3.11.0"
