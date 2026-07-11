"""Broadcaster publishing execution status update envelopes to registered subscribers."""

from __future__ import annotations

import logging
from typing import Callable
from .models import ExecutionEvent, ProgressUpdate


class EventStream:
    """Publishes progress events to interested listeners (like Voice or Desktop UIs)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the EventStream broadcaster.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._subscribers: dict[str, list[Callable[[ProgressUpdate], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[ProgressUpdate], None]) -> None:
        """Registers a callback subscriber for a specific event type or wildcard.

        Args:
            event_type: Specific event type (e.g. 'StepStarted') or '*' for wildcard.
            callback: Action callback executing upon matching notifications.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self._logger.info("Registered callback subscriber", extra={"event_type": event_type})

    def publish(self, update: ProgressUpdate) -> None:
        """Publishes a ProgressUpdate to all matching subscribers.

        Args:
            update: The progress update envelope.
        """
        event_str = update.event_type.value
        self._logger.debug(
            "Broadcasting progress event to subscribers",
            extra={"event": event_str, "execution_id": update.progress.execution_id},
        )

        callbacks = self._subscribers.get(event_str, [])
        for cb in callbacks:
            try:
                cb(update)
            except Exception as cb_err:
                self._logger.error("Error in event callback subscriber execution", exc_info=cb_err)

        wildcard_callbacks = self._subscribers.get("*", [])
        for cb in wildcard_callbacks:
            try:
                cb(update)
            except Exception as cb_err:
                self._logger.error("Error in event wildcard callback subscriber execution", exc_info=cb_err)
