"""Feature Flag Manager (Phase 14.3.4).

Thread-safe manager for feature flag registration, state toggling, evaluation with rollout percentages,
environment/profile restrictions, dependency flag resolution, and evaluation caching.
"""

from datetime import datetime, timezone
import hashlib
import logging
from threading import RLock
from typing import Dict, List, Optional, Set, Tuple

from backend.application.config.models import (
    FeatureEvaluation,
    FeatureFlag,
    FeatureHealth,
    FeatureStatistics,
)

logger = logging.getLogger(__name__)


class FeatureFlagManager:
    """Production thread-safe feature flag evaluation engine."""

    def __init__(self) -> None:
        """Initialize FeatureFlagManager."""
        self._lock = RLock()
        self._features: Dict[str, FeatureFlag] = {}
        self._evaluation_cache: Dict[str, FeatureEvaluation] = {}

        # Metrics
        self._evaluations_count: int = 0
        self._cache_hits: int = 0

    def register_feature(self, feature: FeatureFlag) -> bool:
        """Register or update a feature flag definition.

        Args:
            feature: Target FeatureFlag model.

        Returns:
            bool: True if registered.
        """
        with self._lock:
            self._features[feature.feature_name] = feature
            self._evaluation_cache.clear()
            logger.info("Registered feature flag '%s' (enabled=%s).", feature.feature_name, feature.enabled)
            return True

    def remove_feature(self, feature_name: str) -> bool:
        """Remove a registered feature flag.

        Args:
            feature_name: Target feature flag name.

        Returns:
            bool: True if removed.
        """
        with self._lock:
            if feature_name in self._features:
                del self._features[feature_name]
                self._evaluation_cache.clear()
                logger.info("Removed feature flag '%s'.", feature_name)
                return True
            return False

    def enable(self, feature_name: str) -> bool:
        """Enable a feature flag.

        Args:
            feature_name: Target feature flag name.

        Returns:
            bool: True if enabled.
        """
        with self._lock:
            if feature_name in self._features:
                flag = self._features[feature_name]
                if not flag.enabled:
                    self._features[feature_name] = FeatureFlag(
                        feature_name=flag.feature_name,
                        enabled=True,
                        description=flag.description,
                        rollout_percentage=flag.rollout_percentage,
                        allowed_profiles=flag.allowed_profiles,
                        allowed_environments=flag.allowed_environments,
                        dependencies=flag.dependencies,
                    )
                    self._evaluation_cache.clear()
                    logger.info("Enabled feature flag '%s'.", feature_name)
                return True
            return False

    def disable(self, feature_name: str) -> bool:
        """Disable a feature flag.

        Args:
            feature_name: Target feature flag name.

        Returns:
            bool: True if disabled.
        """
        with self._lock:
            if feature_name in self._features:
                flag = self._features[feature_name]
                if flag.enabled:
                    self._features[feature_name] = FeatureFlag(
                        feature_name=flag.feature_name,
                        enabled=False,
                        description=flag.description,
                        rollout_percentage=flag.rollout_percentage,
                        allowed_profiles=flag.allowed_profiles,
                        allowed_environments=flag.allowed_environments,
                        dependencies=flag.dependencies,
                    )
                    self._evaluation_cache.clear()
                    logger.info("Disabled feature flag '%s'.", feature_name)
                return True
            return False

    def toggle(self, feature_name: str) -> bool:
        """Toggle feature flag status.

        Args:
            feature_name: Target feature flag name.

        Returns:
            bool: Updated boolean status.
        """
        with self._lock:
            if feature_name in self._features:
                flag = self._features[feature_name]
                if flag.enabled:
                    self.disable(feature_name)
                    return False
                else:
                    self.enable(feature_name)
                    return True
            return False

    def _deterministic_rollout_score(self, feature_name: str, instance_id: str) -> float:
        """Compute deterministic rollout score (0.0 to 100.0) from MD5 hash."""
        seed = f"{feature_name}:{instance_id}".encode("utf-8")
        digest = hashlib.md5(seed).hexdigest()
        val = int(digest[:8], 16)
        return (val % 10000) / 100.0

    def evaluate(
        self,
        feature_name: str,
        active_profile_name: str = "development",
        active_env: str = "development",
        instance_id: str = "default",
    ) -> FeatureEvaluation:
        """Evaluate feature flag status with restrictions, dependencies, and rollout rules.

        Args:
            feature_name: Name of target feature.
            active_profile_name: Active profile name string.
            active_env: Active environment string.
            instance_id: Unique instance identifier for rollout hashing.

        Returns:
            FeatureEvaluation: Evaluation result model.
        """
        with self._lock:
            self._evaluations_count += 1
            cache_key = f"{feature_name}:{active_profile_name}:{active_env}:{instance_id}"

            if cache_key in self._evaluation_cache:
                self._cache_hits += 1
                return self._evaluation_cache[cache_key]

            # Missing feature flag check
            if feature_name not in self._features:
                eval_res = FeatureEvaluation(
                    feature_name=feature_name,
                    enabled=False,
                    reason=f"Feature flag '{feature_name}' is not registered.",
                    profile_name=active_profile_name,
                    environment_name=active_env,
                    evaluated_at=datetime.now(timezone.utc),
                )
                self._evaluation_cache[cache_key] = eval_res
                return eval_res

            flag = self._features[feature_name]

            # 1. Base enabled check
            if not flag.enabled:
                eval_res = FeatureEvaluation(
                    feature_name=feature_name,
                    enabled=False,
                    reason=f"Feature flag '{feature_name}' is explicitly disabled.",
                    profile_name=active_profile_name,
                    environment_name=active_env,
                    evaluated_at=datetime.now(timezone.utc),
                )
                self._evaluation_cache[cache_key] = eval_res
                return eval_res

            # 2. Dependencies check
            for dep in flag.dependencies:
                dep_eval = self.evaluate(dep, active_profile_name, active_env, instance_id)
                if not dep_eval.enabled:
                    eval_res = FeatureEvaluation(
                        feature_name=feature_name,
                        enabled=False,
                        reason=f"Required dependency feature flag '{dep}' is disabled.",
                        profile_name=active_profile_name,
                        environment_name=active_env,
                        evaluated_at=datetime.now(timezone.utc),
                    )
                    self._evaluation_cache[cache_key] = eval_res
                    return eval_res

            # 3. Allowed profiles check
            if flag.allowed_profiles:
                allowed_str_profiles = tuple(p.value.lower() for p in flag.allowed_profiles)
                if active_profile_name.lower() not in allowed_str_profiles:
                    eval_res = FeatureEvaluation(
                        feature_name=feature_name,
                        enabled=False,
                        reason=f"Profile '{active_profile_name}' is not in allowed profiles {allowed_str_profiles}.",
                        profile_name=active_profile_name,
                        environment_name=active_env,
                        evaluated_at=datetime.now(timezone.utc),
                    )
                    self._evaluation_cache[cache_key] = eval_res
                    return eval_res

            # 4. Allowed environments check
            if flag.allowed_environments:
                allowed_str_envs = tuple(e.lower() for e in flag.allowed_environments)
                if active_env.lower() not in allowed_str_envs:
                    eval_res = FeatureEvaluation(
                        feature_name=feature_name,
                        enabled=False,
                        reason=f"Environment '{active_env}' is not in allowed environments {allowed_str_envs}.",
                        profile_name=active_profile_name,
                        environment_name=active_env,
                        evaluated_at=datetime.now(timezone.utc),
                    )
                    self._evaluation_cache[cache_key] = eval_res
                    return eval_res

            # 5. Rollout percentage check
            if flag.rollout_percentage < 100.0:
                score = self._deterministic_rollout_score(feature_name, instance_id)
                if score > flag.rollout_percentage:
                    eval_res = FeatureEvaluation(
                        feature_name=feature_name,
                        enabled=False,
                        reason=f"Instance score ({score:.1f}%) exceeds rollout percentage ({flag.rollout_percentage}%).",
                        profile_name=active_profile_name,
                        environment_name=active_env,
                        evaluated_at=datetime.now(timezone.utc),
                    )
                    self._evaluation_cache[cache_key] = eval_res
                    return eval_res

            # All checks passed
            eval_res = FeatureEvaluation(
                feature_name=feature_name,
                enabled=True,
                reason="Feature flag active and all evaluation checks passed.",
                profile_name=active_profile_name,
                environment_name=active_env,
                evaluated_at=datetime.now(timezone.utc),
            )
            self._evaluation_cache[cache_key] = eval_res
            return eval_res

    def is_enabled(
        self,
        feature_name: str,
        active_profile_name: str = "development",
        active_env: str = "development",
        instance_id: str = "default",
    ) -> bool:
        """Check if feature flag is enabled."""
        eval_res = self.evaluate(feature_name, active_profile_name, active_env, instance_id)
        return eval_res.enabled

    def list_features(self) -> Tuple[FeatureFlag, ...]:
        """List all registered feature flags."""
        with self._lock:
            return tuple(self._features.values())

    def health(self) -> FeatureHealth:
        """Get health status of feature flag subsystem."""
        with self._lock:
            return FeatureHealth(
                is_healthy=True,
                issues=(),
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> FeatureStatistics:
        """Get feature flag metrics."""
        with self._lock:
            enabled_count = sum(1 for f in self._features.values() if f.enabled)
            return FeatureStatistics(
                total_features=len(self._features),
                enabled_features=enabled_count,
                evaluations_count=self._evaluations_count,
                cache_hits=self._cache_hits,
            )
