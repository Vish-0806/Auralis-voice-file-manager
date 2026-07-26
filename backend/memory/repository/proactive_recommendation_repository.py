"""ProactiveRecommendation repository mapping for SQL databases."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.repository.base_repository import BaseRepository
from memory.orm.proactive_recommendation import ProactiveRecommendation
from memory.proactive.models import ProactiveRecommendationDomain


class ProactiveRecommendationRepository(BaseRepository[ProactiveRecommendationDomain, ProactiveRecommendation]):
    """Repository mapping ProactiveRecommendation domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, ProactiveRecommendation)

    def _to_domain(self, orm: ProactiveRecommendation) -> ProactiveRecommendationDomain:
        return ProactiveRecommendationDomain(
            id=orm.id,
            user_id=orm.user_id,
            suggestion_text=orm.suggestion_text,
            action_type=orm.action_type,
            confidence_score=orm.confidence_score,
            scoring_details=orm.scoring_details,
            status=orm.status,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: ProactiveRecommendationDomain) -> ProactiveRecommendation:
        return ProactiveRecommendation(
            id=domain.id,
            user_id=domain.user_id,
            suggestion_text=domain.suggestion_text,
            action_type=domain.action_type,
            confidence_score=domain.confidence_score,
            scoring_details=domain.scoring_details,
            status=domain.status,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )
