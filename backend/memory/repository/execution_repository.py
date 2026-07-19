"""ExecutionHistory repository module for Auralis."""

from typing import List
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import ExecutionHistoryDomain
from memory.orm.execution import ExecutionHistory
from memory.repository.base_repository import BaseRepository


class ExecutionRepository(
    BaseRepository[ExecutionHistoryDomain, ExecutionHistory]
):
    """Repository mapping ExecutionHistory domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, ExecutionHistory)

    def _to_domain(self, orm: ExecutionHistory) -> ExecutionHistoryDomain:
        return ExecutionHistoryDomain(
            id=orm.id,
            user_id=orm.user_id,
            action=orm.action,
            status=orm.status,
            duration_ms=orm.duration_ms,
            logs=orm.logs,
            input_parameters=orm.input_parameters,
            output_result=orm.output_result,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: ExecutionHistoryDomain) -> ExecutionHistory:
        return ExecutionHistory(
            id=domain.id,
            user_id=domain.user_id,
            action=domain.action,
            status=domain.status,
            duration_ms=domain.duration_ms,
            logs=domain.logs,
            input_parameters=domain.input_parameters,
            output_result=domain.output_result,
            created_at=domain.created_at,
        )

    def get_recent(self, limit: int) -> List[ExecutionHistoryDomain]:
        """Retrieves the most recent execution history items."""
        return self.list_all(limit=limit, order_by=self.orm_model.created_at.desc())

    def get_failed(self, limit: int) -> List[ExecutionHistoryDomain]:
        """Retrieves the most recent failed execution history items."""
        return self.search(filters={"status": "failed"}, limit=limit, order_by=self.orm_model.created_at.desc())

    def get_successful(self, limit: int) -> List[ExecutionHistoryDomain]:
        """Retrieves the most recent successful execution history items."""
        return self.search(filters={"status": "success"}, limit=limit, order_by=self.orm_model.created_at.desc())
