"""OS power controls implementation."""

from __future__ import annotations

import logging
import os
import subprocess


class PowerController:
    """Controls OS power states (lock, sleep, hibernate, shutdown, restart)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PowerController.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def lock_pc(self) -> None:
        """Locks the PC workspace directly."""

        self._logger.info("Locking computer workstation")
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        else:
            self._logger.warning("Lock PC is only supported on Windows")

    def sleep_pc(self) -> None:
        """Suspends the PC workstation (Sleep state) directly."""

        self._logger.info("Putting computer workstation to sleep")
        if os.name == "nt":
            import ctypes
            # powrprof.dll SetSuspendState(hibernate=0, force=1, disable_wake=0)
            ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        else:
            self._logger.warning("Sleep PC is only supported on Windows")

    def shutdown_pc(self, confirm: bool = False) -> bool:
        """Shuts down the PC.

        Args:
            confirm: Requires confirmation to execute.

        Returns:
            True if action was executed, False if it needs confirmation.
        """

        if not confirm:
            self._logger.info("Shutdown request skipped: confirmation required")
            return False

        self._logger.warning("Executing computer shutdown")
        if os.name == "nt":
            subprocess.run(["shutdown", "/s", "/t", "0"], capture_output=True)
        return True

    def restart_pc(self, confirm: bool = False) -> bool:
        """Restarts the PC.

        Args:
            confirm: Requires confirmation to execute.

        Returns:
            True if action was executed, False if it needs confirmation.
        """

        if not confirm:
            self._logger.info("Restart request skipped: confirmation required")
            return False

        self._logger.warning("Executing computer restart")
        if os.name == "nt":
            subprocess.run(["shutdown", "/r", "/t", "0"], capture_output=True)
        return True

    def hibernate_pc(self, confirm: bool = False) -> bool:
        """Hibernates the PC.

        Args:
            confirm: Requires confirmation to execute.

        Returns:
            True if action was executed, False if it needs confirmation.
        """

        if not confirm:
            self._logger.info("Hibernate request skipped: confirmation required")
            return False

        self._logger.warning("Executing computer hibernation")
        if os.name == "nt":
            import ctypes
            ctypes.windll.powrprof.SetSuspendState(1, 1, 0)
        return True
