"""
Module: backend.os.adapters.windows.adapter
Responsibility: Concrete platform adapter manager implementing IOSPlatformAdapter.
"""
from backend.os.interfaces import IOSPlatformAdapter
class WindowsPlatformAdapter(IOSPlatformAdapter):
    @property
    def platform_name(self) -> str:
        return "windows"
    def validate_platform(self) -> bool:
        return True
