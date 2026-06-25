"""
Module: backend.os.adapters.linux.adapter
Responsibility: Concrete platform adapter manager implementing IOSPlatformAdapter.
"""
from backend.os.interfaces import IOSPlatformAdapter
class LinuxPlatformAdapter(IOSPlatformAdapter):
    @property
    def platform_name(self) -> str:
        return "linux"
    def validate_platform(self) -> bool:
        return True
