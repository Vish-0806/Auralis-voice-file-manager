"""Shared mock utilities for Auralis unit and runtime tests."""

from typing import Any, Optional


class MockResult:
    """Mock execution result payload."""

    def __init__(
        self,
        success: bool = True,
        execution_time: float = 0.01,
        response: str = "Execution succeeded",
        error: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        self.success = success
        self.execution_time = execution_time
        self.response = response
        self.error = error
        self.data = data or {}


class MockDispatcher:
    """Mock dispatcher that simulates a series of successes/failures."""

    def __init__(self, failure_count: int = 0) -> None:
        self.failure_count = failure_count
        self.calls = 0

    def dispatch(self, plan: Any) -> MockResult:
        self.calls += 1
        is_success = self.calls > self.failure_count
        return MockResult(
            success=is_success,
            execution_time=0.01,
            response="Execution succeeded" if is_success else "",
            error="Mocked execution failure" if not is_success else None,
            data={},
        )
