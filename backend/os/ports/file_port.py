"""
Module: backend.os.ports.file_port
Responsibility: Abstract port interface defining OS file system actions.
"""
from abc import ABC, abstractmethod
class FilePort(ABC):
    @abstractmethod
    def copy_file(self, src: str, dest: str) -> bool:
        pass
