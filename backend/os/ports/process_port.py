"""
Module: backend.os.ports.process_port
Responsibility: Abstract port interface defining process control and list actions.
"""
from abc import ABC, abstractmethod
class ProcessPort(ABC):
    @abstractmethod
    def terminate_process(self, pid: int) -> bool:
        pass
