"""
Module: backend.os.adapters.windows.files
Responsibility: Concrete implementation of FilePort for Windows.
"""
from backend.os.ports.file_port import FilePort
class WindowsFileAdapter(FilePort):
    def copy_file(self, src: str, dest: str) -> bool:
        pass
