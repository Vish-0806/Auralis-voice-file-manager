"""
Module: backend.os.adapters.macos.adapter
Responsibility: Concrete platform adapter manager implementing IOSPlatformAdapter.
"""
from backend.os.interfaces import IOSPlatformAdapter
class MacosPlatformAdapter(IOSPlatformAdapter):
    @property
    def platform_name(self) -> str:
        return "macos"
    def validate_platform(self) -> bool:
        return True
