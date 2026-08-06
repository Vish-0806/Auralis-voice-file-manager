/**
 * Feature Flag Manager & Evaluation Engine (Phase 16.3.4).
 *
 * Implements feature flag registration, enable/disable/toggle controls, dependency evaluation,
 * profile & environment restrictions, deterministic rollout percentage calculation,
 * evaluation caching, and diagnostic reporting.
 */

import {
  createFeatureEvaluation,
  createFeatureFlag,
  createFeatureHealth,
  createFeatureStatistics,
  FeatureEvaluation,
  FeatureFlag,
  FeatureHealth,
  FeatureStatistics,
} from './models';
import { ConfigurationProviderException } from './exceptions';

export class FeatureFlagManager {
  private readonly _features = new Map<string, FeatureFlag>();
  private readonly _evaluationCache = new Map<string, FeatureEvaluation>();

  private _evaluations = 0;
  private _enabledEvaluations = 0;
  private _disabledEvaluations = 0;
  private _cachedEvaluations = 0;

  public registerFeature(feature: FeatureFlag): void {
    if (!feature) {
      throw new ConfigurationProviderException('Feature flag cannot be null or undefined.');
    }
    const name = feature.featureName.trim();
    if (!name) {
      throw new ConfigurationProviderException('Feature name cannot be empty.');
    }
    if (this._features.has(name)) {
      throw new ConfigurationProviderException(`Feature flag '${name}' is already registered.`);
    }

    this._features.set(name, feature);
    this._evaluationCache.clear();
  }

  public removeFeature(featureName: string): boolean {
    const name = featureName.trim();
    const removed = this._features.delete(name);
    if (removed) {
      this._evaluationCache.clear();
    }
    return removed;
  }

  public enable(featureName: string): void {
    const name = featureName.trim();
    const target = this._features.get(name);
    if (!target) {
      throw new ConfigurationProviderException(`Feature flag '${featureName}' is not registered.`);
    }
    this._features.set(name, createFeatureFlag({ ...target, enabled: true }));
    this._evaluationCache.clear();
  }

  public disable(featureName: string): void {
    const name = featureName.trim();
    const target = this._features.get(name);
    if (!target) {
      throw new ConfigurationProviderException(`Feature flag '${featureName}' is not registered.`);
    }
    this._features.set(name, createFeatureFlag({ ...target, enabled: false }));
    this._evaluationCache.clear();
  }

  public toggle(featureName: string): boolean {
    const name = featureName.trim();
    const target = this._features.get(name);
    if (!target) {
      throw new ConfigurationProviderException(`Feature flag '${featureName}' is not registered.`);
    }
    const nextState = !target.enabled;
    this._features.set(name, createFeatureFlag({ ...target, enabled: nextState }));
    this._evaluationCache.clear();
    return nextState;
  }

  public evaluate(
    featureName: string,
    context?: { profileName?: string; environmentName?: string; userId?: string },
  ): FeatureEvaluation {
    this._evaluations++;
    const name = featureName.trim();
    const cacheKey = `${name}:${context?.profileName ?? ''}:${context?.environmentName ?? ''}:${context?.userId ?? ''}`;

    if (this._evaluationCache.has(cacheKey)) {
      this._cachedEvaluations++;
      return this._evaluationCache.get(cacheKey)!;
    }

    const feature = this._features.get(name);
    if (!feature) {
      this._disabledEvaluations++;
      const res = createFeatureEvaluation({
        featureName: name,
        enabled: false,
        reason: 'Feature not registered.',
        profileName: context?.profileName,
        environmentName: context?.environmentName,
      });
      this._evaluationCache.set(cacheKey, res);
      return res;
    }

    if (!feature.enabled) {
      this._disabledEvaluations++;
      const res = createFeatureEvaluation({
        featureName: name,
        enabled: false,
        reason: 'Feature is explicitly disabled.',
        profileName: context?.profileName,
        environmentName: context?.environmentName,
      });
      this._evaluationCache.set(cacheKey, res);
      return res;
    }

    if (
      feature.allowedProfiles &&
      feature.allowedProfiles.length > 0 &&
      context?.profileName &&
      !feature.allowedProfiles.includes(context.profileName)
    ) {
      this._disabledEvaluations++;
      const res = createFeatureEvaluation({
        featureName: name,
        enabled: false,
        reason: `Profile '${context.profileName}' is not in allowed profiles.`,
        profileName: context?.profileName,
        environmentName: context?.environmentName,
      });
      this._evaluationCache.set(cacheKey, res);
      return res;
    }

    if (
      feature.allowedEnvironments &&
      feature.allowedEnvironments.length > 0 &&
      context?.environmentName &&
      !feature.allowedEnvironments.includes(context.environmentName)
    ) {
      this._disabledEvaluations++;
      const res = createFeatureEvaluation({
        featureName: name,
        enabled: false,
        reason: `Environment '${context.environmentName}' is not in allowed environments.`,
        profileName: context?.profileName,
        environmentName: context?.environmentName,
      });
      this._evaluationCache.set(cacheKey, res);
      return res;
    }

    if (feature.dependencies && feature.dependencies.length > 0) {
      for (const dep of feature.dependencies) {
        const depEval = this.evaluate(dep, context);
        if (!depEval.enabled) {
          this._disabledEvaluations++;
          const res = createFeatureEvaluation({
            featureName: name,
            enabled: false,
            reason: `Dependency requirement '${dep}' not met.`,
            profileName: context?.profileName,
            environmentName: context?.environmentName,
          });
          this._evaluationCache.set(cacheKey, res);
          return res;
        }
      }
    }

    if (feature.rolloutPercentage !== undefined && feature.rolloutPercentage < 100) {
      const userSeed = context?.userId ?? 'default_user';
      const hash = this.deterministicHash(userSeed);
      if (hash >= feature.rolloutPercentage) {
        this._disabledEvaluations++;
        const res = createFeatureEvaluation({
          featureName: name,
          enabled: false,
          reason: `User excluded by rollout percentage (${hash}% >= ${feature.rolloutPercentage}%).`,
          profileName: context?.profileName,
          environmentName: context?.environmentName,
        });
        this._evaluationCache.set(cacheKey, res);
        return res;
      }
    }

    this._enabledEvaluations++;
    const res = createFeatureEvaluation({
      featureName: name,
      enabled: true,
      reason: 'Feature enabled.',
      profileName: context?.profileName,
      environmentName: context?.environmentName,
    });
    this._evaluationCache.set(cacheKey, res);
    return res;
  }

  public listFeatures(): ReadonlyArray<FeatureFlag> {
    return Object.freeze(Array.from(this._features.values()));
  }

  public statistics(): FeatureStatistics {
    return createFeatureStatistics({
      evaluations: this._evaluations,
      enabledEvaluations: this._enabledEvaluations,
      disabledEvaluations: this._disabledEvaluations,
      cachedEvaluations: this._cachedEvaluations,
    });
  }

  public health(): FeatureHealth {
    const features = Array.from(this._features.values());
    const enabled = features.filter((f) => f.enabled).length;
    return createFeatureHealth({
      healthy: true,
      totalFeatures: features.length,
      enabledFeatures: enabled,
      disabledFeatures: features.length - enabled,
    });
  }

  public clear(): void {
    this._features.clear();
    this._evaluationCache.clear();
  }

  private deterministicHash(seed: string): number {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = (hash << 5) - hash + seed.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash) % 100;
  }
}
