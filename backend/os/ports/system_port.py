"""
Module: backend.os.ports.system_port
Responsibility: Abstract port interface defining hardware info and metrics retrieval.
"""
from abc import ABC, abstractmethod
class SystemPort(ABC):
    @abstractmethod
    def get_cpu_load(self) -> float:
        pass
