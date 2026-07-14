"""Scheduler for running periodic routine learning analysis."""

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class LearningScheduler:
    """Schedules background execution of routine patterns extraction."""

    def __init__(self, callback: Callable[[], None], interval_seconds: float = 3600.0) -> None:
        """Initializes LearningScheduler.

        Args:
            callback: The method or function to run periodically.
            interval_seconds: Run interval time duration.
        """
        self._callback = callback
        self._interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Launches the background daemon thread loop."""
        if self._thread is not None:
            logger.warning("LearningScheduler background thread already running.")
            return

        logger.info(f"Starting LearningScheduler thread (interval: {self._interval}s).")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="RoutineLearningScheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Halts the background loop and joins the thread."""
        if self._thread is None:
            return

        logger.info("Stopping LearningScheduler background thread.")
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self._thread = None

    def _run_loop(self) -> None:
        """Core loop executing the callback and sleeping until stopped."""
        while not self._stop_event.is_set():
            try:
                self._callback()
            except Exception as e:
                logger.error(f"Error in routine learning scheduler callback execution: {e}")
            # Wait for next interval or until stop event triggers
            self._stop_event.wait(self._interval)
        logger.info("LearningScheduler loop ended.")
        
    @property
    def is_running(self) -> bool:
        """Checks if the scheduler background thread is currently active."""
        return self._thread is not None and self._thread.is_alive()
