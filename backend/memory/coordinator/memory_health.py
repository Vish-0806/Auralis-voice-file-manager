"""Memory Platform Health diagnostics and stats module."""

import logging
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from memory.database.session import SessionLocal

logger = logging.getLogger(__name__)


class MemoryHealth:
    """Diagnoses memory platform health status and aggregates runtime statistics."""

    def __init__(self, registry: Any, session_factory: Optional[Any] = None) -> None:
        """Initializes MemoryHealth.

        Args:
            registry: Injected MemoryRegistry container class.
            session_factory: Optional custom session creator callable.
        """
        self._registry = registry
        self._session_factory = session_factory or SessionLocal

    def check_health(self) -> Dict[str, Any]:
        """Performs database, repository, cache, and service status diagnostic checks.

        Returns:
            Dictionary containing health outcomes for database, repository, cache, services.
        """
        status = {
            "status": "healthy",
            "database": "healthy",
            "repository": "healthy",
            "cache": "healthy",
            "services": "healthy",
        }

        # 1. Database Connection Check
        db = None
        try:
            db = self._session_factory()
            db.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Health check database connection failure: {e}")
            status["database"] = f"unhealthy: {e}"
            status["status"] = "unhealthy"
        finally:
            if db:
                db.close()

        # 2. Repository Check
        try:
            pref_service = self._registry.get("preferences")
            if pref_service:
                # Run query on repo
                pref_service._engine._repository.search({"id": -999})
            else:
                status["repository"] = "unhealthy: PreferenceService missing from registry."
                status["status"] = "unhealthy"
        except Exception as e:
            logger.error(f"Health check repository failure: {e}")
            status["repository"] = f"unhealthy: {e}"
            status["status"] = "unhealthy"

        # 3. Cache Check
        try:
            ctx_service = self._registry.get("context")
            if ctx_service:
                cache = ctx_service._manager._cache
                # Check setting/retrieval
                cache.set(-999, "health_check", {"k": "v"})
                if cache.get(-999, "health_check") != {"k": "v"}:
                    raise RuntimeError("Cache read/write mismatch")
                cache.invalidate(-999, "health_check")
            else:
                status["cache"] = "unhealthy: ContextService missing from registry."
                status["status"] = "unhealthy"
        except Exception as e:
            logger.error(f"Health check cache failure: {e}")
            status["cache"] = f"unhealthy: {e}"
            status["status"] = "unhealthy"

        # 4. Service Coverage Check
        required = ["preferences", "context", "workspace", "learning", "personalization"]
        missing = [r for r in required if self._registry.get(r) is None]
        if missing:
            status["services"] = f"unhealthy: missing required services {missing}"
            status["status"] = "unhealthy"

        return status

    def get_metrics(self, user_id: int) -> Dict[str, Any]:
        """Aggregates memory usage stats for a user.

        Args:
            user_id: Owner user ID.

        Returns:
            Dictionary containing counts for preferences, context items, profiles, routines.
        """
        metrics = {
            "preferences_count": 0,
            "active_context_keys": 0,
            "workspace_profiles_count": 0,
            "learned_routines_count": 0,
            "total_execution_logs": 0,
        }

        # 1. Preferences Count
        try:
            pref_service = self._registry.get("preferences")
            if pref_service:
                prefs = pref_service._engine._repository.search({"user_id": user_id})
                metrics["preferences_count"] = len(prefs)
        except Exception:
            pass

        # 2. Context Keys Count
        try:
            ctx_service = self._registry.get("context")
            if ctx_service:
                # Load active context map
                ctx_map = ctx_service.load(user_id, "dummy_metrics_session")
                metrics["active_context_keys"] = len(ctx_map)
        except Exception:
            pass

        # 3. Workspaces Count
        try:
            ws_service = self._registry.get("workspace")
            if ws_service:
                metrics["workspace_profiles_count"] = len(ws_service.list(user_id))
        except Exception:
            pass

        # 4. Learning Metrics
        try:
            lr_service = self._registry.get("learning")
            if lr_service:
                metrics["learned_routines_count"] = len(lr_service.list(user_id))
                executions = lr_service._engine._execution_repository.search({"user_id": user_id})
                metrics["total_execution_logs"] = len(executions)
        except Exception:
            pass

        return metrics
