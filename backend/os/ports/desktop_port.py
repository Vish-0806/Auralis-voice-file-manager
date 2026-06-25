"""
Module: backend.os.ports.desktop_port
Responsibility: Abstract port interface defining GUI window and display actions.
"""
from abc import ABC, abstractmethod
class DesktopPort(ABC):
    @abstractmethod
    def set_window_focus(self, hwnd: int) -> bool:
        pass
