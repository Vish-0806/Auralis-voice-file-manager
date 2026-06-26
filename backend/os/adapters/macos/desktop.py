"""
Module: backend.os.adapters.macos.desktop
Responsibility: Concrete implementation of DesktopPort for Macos.
"""
from ...ports.desktop_port import DesktopPort
class MacosDesktopAdapter(DesktopPort):
    def set_window_focus(self, hwnd: int) -> bool:
        pass
