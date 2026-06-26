"""
Module: backend.os.adapters.macos.system
Responsibility: Concrete implementation of SystemPort for Macos.
"""
from ...ports.system_port import SystemPort
class MacosSystemAdapter(SystemPort):
    def get_cpu_load(self) -> float:
        pass
