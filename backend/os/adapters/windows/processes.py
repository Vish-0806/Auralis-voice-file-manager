"""
Module: backend.os.adapters.windows.processes
Responsibility: Concrete implementation of ProcessPort for Windows.
"""
from os.ports.process_port import ProcessPort
class WindowsProcessAdapter(ProcessPort):
    def terminate_process(self, pid: int) -> bool:
        pass
