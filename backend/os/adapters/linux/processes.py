"""
Module: backend.os.adapters.linux.processes
Responsibility: Concrete implementation of ProcessPort for Linux.
"""
from ...ports.process_port import ProcessPort
class LinuxProcessAdapter(ProcessPort):
    def terminate_process(self, pid: int) -> bool:
        pass
