"""
Module: backend.os.adapters.macos.files
Responsibility: Concrete implementation of FilePort for Macos.
"""
from ...ports.file_port import FilePort
class MacosFileAdapter(FilePort):
    def copy_file(self, src: str, dest: str) -> bool:
        pass
