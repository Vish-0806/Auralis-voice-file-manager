"""
Module: backend.os.adapters.macos.processes
Responsibility: Concrete implementation of ProcessPort for Macos.
"""
from os.ports.process_port import ProcessPort
class MacosProcessAdapter(ProcessPort):
    def terminate_process(self, pid: int) -> bool:
        pass
