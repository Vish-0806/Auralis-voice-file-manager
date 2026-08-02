"""Task Scheduler for the Auralis Task Management Runtime (Phase 12.5).

Responsible for priority-queued task scheduling, delayed task handling, and recurring schedules.
Does not contain task execution logic.
"""

from datetime import datetime, timezone
import heapq
import threading
import time
from typing import Dict, List, Optional

from brain.execution.task.interfaces import ITaskScheduler
from brain.execution.task.task_models import (
    TaskExecution,
    TaskPriority,
    TaskProgress,
    TaskRequest,
    TaskStatus,
)

PRIORITY_WEIGHT = {
    TaskPriority.CRITICAL: 4,
    TaskPriority.HIGH: 3,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 1,
}


class TaskScheduler(ITaskScheduler):
    """Priority-queued task scheduler with support for delayed and recurring task scheduling."""

    def __init__(self) -> None:
        """Initializes TaskScheduler with thread-safe priority queue."""
        self._lock = threading.RLock()
        # Min-heap items: (-priority_weight, created_timestamp, task_id, TaskExecution, TaskRequest)
        self._queue: List[tuple] = []
        self._task_map: Dict[str, TaskExecution] = {}
        self._request_map: Dict[str, TaskRequest] = {}

    def enqueue(self, request: TaskRequest) -> TaskExecution:
        """Enqueue a TaskRequest into the priority queue.

        Args:
            request: TaskRequest object.

        Returns:
            TaskExecution object representing queued task state.
        """
        with self._lock:
            progress = TaskProgress(task_id=request.task_id, status_message="Queued")
            execution = TaskExecution(
                task_id=request.task_id,
                status=TaskStatus.QUEUED,
                progress=progress,
                metadata={"priority": request.priority.value, "mode": request.mode.value},
            )

            prio_weight = PRIORITY_WEIGHT.get(request.priority, 2)
            created_ts = request.created_at.timestamp()
            # Push into min-heap with negative priority_weight so highest priority dequeues first
            heapq.heappush(self._queue, (-prio_weight, created_ts, request.task_id, execution, request))
            self._task_map[request.task_id] = execution
            self._request_map[request.task_id] = request

            return execution

    def dequeue(self) -> Optional[TaskExecution]:
        """Dequeue the highest priority ready TaskExecution.

        Returns:
            Highest priority TaskExecution or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None

            now_ts = datetime.now(timezone.utc).timestamp()
            # Filter and pop ready task (considering delay_seconds)
            temp_list: List[tuple] = []
            selected_item: Optional[tuple] = None

            while self._queue:
                item = heapq.heappop(self._queue)
                _, created_ts, _, execution, req = item

                ready_at_ts = created_ts + req.delay_seconds
                if now_ts >= ready_at_ts:
                    selected_item = item
                    break
                else:
                    temp_list.append(item)

            # Re-push delayed non-ready items
            for delayed_item in temp_list:
                heapq.heappush(self._queue, delayed_item)

            if selected_item:
                _, _, t_id, execution, req = selected_item
                self._task_map.pop(t_id, None)
                self._request_map.pop(t_id, None)
                return execution

            return None

    def peek_queue(self) -> List[TaskExecution]:
        """View active priority queue items ordered by priority.

        Returns:
            List of TaskExecution items currently queued.
        """
        with self._lock:
            sorted_items = sorted(self._queue, key=lambda x: (x[0], x[1]))
            return [item[3] for item in sorted_items]

    def remove_task(self, task_id: str) -> bool:
        """Remove a queued task by task_id.

        Args:
            task_id: Task ID to remove.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            if task_id not in self._task_map:
                return False

            self._queue = [item for item in self._queue if item[2] != task_id]
            heapq.heapify(self._queue)
            self._task_map.pop(task_id, None)
            self._request_map.pop(task_id, None)
            return True
