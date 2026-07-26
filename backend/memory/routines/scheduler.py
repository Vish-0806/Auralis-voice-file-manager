"""Routine Scheduler running delayed, recurring, startup, and shutdown tasks."""

import asyncio
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class RoutineScheduler:
    """Asynchronously schedules recurring, delayed, and conditional automations."""

    def __init__(self) -> None:
        self._running_tasks: Dict[int, asyncio.Task] = {}
        self._startup_routines: List[Any] = []
        self._shutdown_routines: List[Any] = []

    def schedule_recurring(self, routine: Any, interval_seconds: float, callback: Callable[[Any], Any]) -> None:
        """Schedules a recurring routine execution on a regular loop interval."""
        async def loop_runner():
            while True:
                await asyncio.sleep(interval_seconds)
                try:
                    # Execute callback (can be async or sync)
                    res = callback(routine)
                    if asyncio.iscoroutine(res):
                        await res
                except asyncio.CancelledError:
                    break
                except Exception:
                    logger.error(f"Error running scheduled recurring routine ID {getattr(routine, 'id', None)}", exc_info=True)

        task = asyncio.create_task(loop_runner())
        routine_id = getattr(routine, "id", id(routine))
        self._running_tasks[routine_id] = task

    def schedule_delayed(self, routine: Any, delay_seconds: float, callback: Callable[[Any], Any]) -> None:
        """Schedules a one-off delayed routine execution."""
        async def delayed_runner():
            try:
                await asyncio.sleep(delay_seconds)
                res = callback(routine)
                if asyncio.iscoroutine(res):
                    await res
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.error(f"Error running scheduled delayed routine ID {getattr(routine, 'id', None)}", exc_info=True)

        task = asyncio.create_task(delayed_runner())
        routine_id = getattr(routine, "id", id(routine))
        self._running_tasks[routine_id] = task

    def register_startup_routine(self, routine: Any) -> None:
        """Registers a routine to run immediately on application startup."""
        self._startup_routines.append(routine)

    def register_shutdown_routine(self, routine: Any) -> None:
        """Registers a routine to run prior to application shutdown."""
        self._shutdown_routines.append(routine)

    async def execute_startup_routines(self, callback: Callable[[Any], Any]) -> None:
        """Executes all startup-registered routines."""
        for r in self._startup_routines:
            try:
                res = callback(r)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                logger.error("Startup routine execution failed", exc_info=True)

    async def execute_shutdown_routines(self, callback: Callable[[Any], Any]) -> None:
        """Executes all shutdown-registered routines."""
        for r in self._shutdown_routines:
            try:
                res = callback(r)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                logger.error("Shutdown routine execution failed", exc_info=True)

    def cancel_routine(self, routine_id: int) -> bool:
        """Cancels any active running scheduling loop for the given routine ID."""
        task = self._running_tasks.pop(routine_id, None)
        if task:
            task.cancel()
            return True
        return False
