"""Thread-safe inactivity timer for ending inactive conversation sessions."""

import threading
from typing import Callable, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class InactivityTimer:
    """Invokes a callback after a configured duration of inactivity.

    Runs in a background daemon thread and can be reset or cancelled dynamically.
    """

    def __init__(self, timeout_seconds: float, callback: Callable[[], None]) -> None:
        """Initializes the InactivityTimer.

        Args:
            timeout_seconds: Duration in seconds to wait before timeout.
            callback: Function to invoke when the timer expires.
        """
        self.timeout_seconds = timeout_seconds
        self.callback = callback
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Starts or resets the inactivity timer.

        If a timer is already running, it is cancelled and replaced with a new one.
        """
        with self._lock:
            self.cancel_locked()
            if self.timeout_seconds > 0:
                logger.debug(
                    "Starting inactivity timer: %.1f seconds",
                    self.timeout_seconds,
                )
                self._timer = threading.Timer(self.timeout_seconds, self._trigger)
                self._timer.daemon = True
                self._timer.start()

    def reset(self) -> None:
        """Resets the inactivity timer back to its full duration."""
        self.start()

    def cancel(self) -> None:
        """Cancels the running timer, preventing the callback from firing."""
        with self._lock:
            self.cancel_locked()

    def cancel_locked(self) -> None:
        """Internal method to cancel timer while lock is held."""
        if self._timer is not None:
            logger.debug("Cancelling active inactivity timer")
            self._timer.cancel()
            self._timer = None

    def _trigger(self) -> None:
        """Executes when the background timer thread expires."""
        logger.info("Inactivity timer expired")
        try:
            self.callback()
        except Exception as e:
            logger.exception("Error during inactivity timeout callback: %s", e)
        finally:
            with self._lock:
                self._timer = None
