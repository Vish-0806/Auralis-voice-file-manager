"""
Module: backend.os.adapters.linux.files
Responsibility: Concrete implementation of FilePort for Linux.
"""
from os.ports.file_port import FilePort
class LinuxFileAdapter(FilePort):
    def copy_file(self, src: str, dest: str) -> bool:
        pass
