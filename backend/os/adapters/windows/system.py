"""
Module: backend.os.adapters.windows.system
Responsibility: Concrete implementation of SystemPort for Windows.
"""
from os.ports.system_port import SystemPort
class WindowsSystemAdapter(SystemPort):
    def get_cpu_load(self) -> float:
        pass
