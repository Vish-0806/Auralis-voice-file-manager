"""
Module: backend.os.adapters.linux.system
Responsibility: Concrete implementation of SystemPort for Linux.
"""
from os.ports.system_port import SystemPort
class LinuxSystemAdapter(SystemPort):
    def get_cpu_load(self) -> float:
        pass
