import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationProvider,
  ConfigurationProviderException,
  ConfigurationRuntime,
  createConfigurationProfileDefinition,
  createConfigurationProfileSnapshot,
  createFeatureEvaluation,
  createFeatureFlag,
  createFeatureHealth,
  createFeatureStatistics,
  createProfileHealth,
  createProfileStatistics,
  FeatureFlagManager,
  MemoryConfigurationSource,
  ProfileManager,
  resetConfigurationProvider,
  resetConfigurationRuntime,
} from '../../src/runtime/config';

describe('Phase 16.3.4 — Frontend Configuration Profiles & Feature Flag Runtime', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable FeatureFlag model', () => {
      const feature = createFeatureFlag({
        featureName: 'voice.transcription',
        enabled: true,
        description: 'Voice file transcription',
        rolloutPercentage: 50,
        allowedProfiles: ['production'],
        allowedEnvironments: ['prod'],
        dependencies: ['audio.engine'],
      });

      expect(feature.featureName).toBe('voice.transcription');
      expect(feature.enabled).toBe(true);
      expect(feature.rolloutPercentage).toBe(50);
      expect(Object.isFrozen(feature)).toBe(true);
      expect(Object.isFrozen(feature.allowedProfiles)).toBe(true);
      expect(Object.isFrozen(feature.allowedEnvironments)).toBe(true);
      expect(Object.isFrozen(feature.dependencies)).toBe(true);
    });

    it('should create immutable FeatureEvaluation model', () => {
      const evaluation = createFeatureEvaluation({
        featureName: 'voice.transcription',
        enabled: true,
        reason: 'Feature enabled.',
        profileName: 'production',
      });

      expect(evaluation.featureName).toBe('voice.transcription');
      expect(evaluation.enabled).toBe(true);
      expect(evaluation.reason).toBe('Feature enabled.');
      expect(Object.isFrozen(evaluation)).toBe(true);
    });

    it('should create immutable FeatureStatistics and FeatureHealth models', () => {
      const stats = createFeatureStatistics({ evaluations: 10, enabledEvaluations: 8 });
      expect(stats.evaluations).toBe(10);
      expect(stats.enabledEvaluations).toBe(8);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createFeatureHealth({ totalFeatures: 5, enabledFeatures: 3 });
      expect(health.totalFeatures).toBe(5);
      expect(health.enabledFeatures).toBe(3);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable ConfigurationProfileDefinition model', () => {
      const profile = createConfigurationProfileDefinition({
        profileType: 'custom',
        profileName: 'staging',
        overrides: { 'api.url': 'https://staging.api.com' },
      });

      expect(profile.profileName).toBe('staging');
      expect(profile.overrides['api.url']).toBe('https://staging.api.com');
      expect(Object.isFrozen(profile)).toBe(true);
      expect(Object.isFrozen(profile.overrides)).toBe(true);
    });

    it('should create immutable ConfigurationProfileSnapshot model', () => {
      const snapshot = createConfigurationProfileSnapshot({
        activeProfileName: 'staging',
        registeredProfiles: ['development', 'staging'],
      });

      expect(snapshot.activeProfileName).toBe('staging');
      expect(snapshot.registeredProfiles).toContain('staging');
      expect(Object.isFrozen(snapshot)).toBe(true);
      expect(Object.isFrozen(snapshot.registeredProfiles)).toBe(true);
    });

    it('should create immutable ProfileStatistics and ProfileHealth models', () => {
      const stats = createProfileStatistics({ registrations: 3, activations: 2 });
      expect(stats.registrations).toBe(3);
      expect(stats.activations).toBe(2);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createProfileHealth({ activeProfileName: 'production', totalProfiles: 3 });
      expect(health.activeProfileName).toBe('production');
      expect(health.totalProfiles).toBe(3);
      expect(Object.isFrozen(health)).toBe(true);
    });
  });

  describe('2. ProfileManager Engine', () => {
    it('should register default profiles (development, testing, production with production active)', () => {
      const pm = new ProfileManager();
      const profiles = pm.listProfiles();

      expect(profiles.length).toBe(3);
      expect(pm.getActiveProfile()?.profileName).toBe('production');
    });

    it('should register custom profile and reject duplicate profile name', () => {
      const pm = new ProfileManager();
      const custom = createConfigurationProfileDefinition({ profileType: 'custom', profileName: 'qa' });

      pm.registerProfile(custom);
      expect(pm.getProfile('qa')).toBe(custom);

      expect(() => pm.registerProfile(custom)).toThrow(ConfigurationProviderException);
    });

    it('should reject null or empty profile name', () => {
      const pm = new ProfileManager();
      expect(() => pm.registerProfile(null as any)).toThrow(ConfigurationProviderException);
      expect(() =>
        pm.registerProfile(
          createConfigurationProfileDefinition({ profileType: 'custom', profileName: '   ' }),
        ),
      ).toThrow(ConfigurationProviderException);
    });

    it('should activate profile and update active profile state', () => {
      const pm = new ProfileManager();
      pm.activateProfile('development');

      expect(pm.getActiveProfile()?.profileName).toBe('development');
      expect(pm.getProfile('development')?.active).toBe(true);
      expect(pm.getProfile('production')?.active).toBe(false);
    });

    it('should throw ConfigurationProviderException when activating unregistered profile', () => {
      const pm = new ProfileManager();
      expect(() => pm.activateProfile('unknown_profile')).toThrow(ConfigurationProviderException);
    });

    it('should merge parent profile overrides before child profile overrides (inheritance)', () => {
      const pm = new ProfileManager();

      const base = createConfigurationProfileDefinition({
        profileType: 'base',
        profileName: 'base_prof',
        overrides: { 'a': 1, 'b': 2 },
      });

      const child = createConfigurationProfileDefinition({
        profileType: 'child',
        profileName: 'child_prof',
        parentProfileName: 'base_prof',
        active: true,
        overrides: { 'b': 20, 'c': 30 },
      });

      pm.registerProfile(base);
      pm.registerProfile(child);

      const merged = pm.getMergedOverrides();
      expect(merged).toEqual({ a: 1, b: 20, c: 30 });
    });

    it('should produce complete profile snapshot, health, and statistics', () => {
      const pm = new ProfileManager();
      const snapshot = pm.createSnapshot();

      expect(snapshot.activeProfileName).toBe('production');
      expect(snapshot.registeredProfiles).toContain('production');

      const stats = pm.statistics();
      expect(stats.registrations).toBeGreaterThan(0);

      const health = pm.health();
      expect(health.healthy).toBe(true);
      expect(health.totalProfiles).toBe(3);
    });
  });

  describe('3. FeatureFlagManager Engine', () => {
    it('should register feature flag and evaluate enabled status', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({ featureName: 'dark_mode', enabled: true });

      ffm.registerFeature(flag);
      const evalRes = ffm.evaluate('dark_mode');

      expect(evalRes.enabled).toBe(true);
      expect(evalRes.reason).toBe('Feature enabled.');
    });

    it('should reject duplicate feature flag registration', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({ featureName: 'dark_mode' });

      ffm.registerFeature(flag);
      expect(() => ffm.registerFeature(flag)).toThrow(ConfigurationProviderException);
    });

    it('should reject null or empty feature name', () => {
      const ffm = new FeatureFlagManager();
      expect(() => ffm.registerFeature(null as any)).toThrow(ConfigurationProviderException);
      expect(() => ffm.registerFeature(createFeatureFlag({ featureName: '   ' }))).toThrow(
        ConfigurationProviderException,
      );
    });

    it('should evaluate unregistered feature flag as disabled', () => {
      const ffm = new FeatureFlagManager();
      const evalRes = ffm.evaluate('unknown_feature');

      expect(evalRes.enabled).toBe(false);
      expect(evalRes.reason).toContain('not registered');
    });

    it('should throw ConfigurationProviderException when enabling or disabling unregistered feature', () => {
      const ffm = new FeatureFlagManager();
      expect(() => ffm.enable('unknown')).toThrow(ConfigurationProviderException);
      expect(() => ffm.disable('unknown')).toThrow(ConfigurationProviderException);
      expect(() => ffm.toggle('unknown')).toThrow(ConfigurationProviderException);
    });

    it('should enable, disable, and toggle feature flag', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({ featureName: 'beta_ui', enabled: false });

      ffm.registerFeature(flag);
      expect(ffm.evaluate('beta_ui').enabled).toBe(false);

      ffm.enable('beta_ui');
      expect(ffm.evaluate('beta_ui').enabled).toBe(true);

      ffm.disable('beta_ui');
      expect(ffm.evaluate('beta_ui').enabled).toBe(false);

      const toggledState = ffm.toggle('beta_ui');
      expect(toggledState).toBe(true);
      expect(ffm.evaluate('beta_ui').enabled).toBe(true);
    });

    it('should enforce profile restrictions during evaluation', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({
        featureName: 'dev_tools',
        enabled: true,
        allowedProfiles: ['development', 'testing'],
      });

      ffm.registerFeature(flag);

      const devEval = ffm.evaluate('dev_tools', { profileName: 'development' });
      expect(devEval.enabled).toBe(true);

      const prodEval = ffm.evaluate('dev_tools', { profileName: 'production' });
      expect(prodEval.enabled).toBe(false);
      expect(prodEval.reason).toContain('allowed profiles');
    });

    it('should enforce environment restrictions during evaluation', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({
        featureName: 'prod_analytics',
        enabled: true,
        allowedEnvironments: ['production'],
      });

      ffm.registerFeature(flag);

      const prodEval = ffm.evaluate('prod_analytics', { environmentName: 'production' });
      expect(prodEval.enabled).toBe(true);

      const devEval = ffm.evaluate('prod_analytics', { environmentName: 'staging' });
      expect(devEval.enabled).toBe(false);
      expect(devEval.reason).toContain('allowed environments');
    });

    it('should evaluate feature dependencies recursively', () => {
      const ffm = new FeatureFlagManager();
      const baseFlag = createFeatureFlag({ featureName: 'core_engine', enabled: true });
      const depFlag = createFeatureFlag({
        featureName: 'ai_summarizer',
        enabled: true,
        dependencies: ['core_engine'],
      });

      ffm.registerFeature(baseFlag);
      ffm.registerFeature(depFlag);

      expect(ffm.evaluate('ai_summarizer').enabled).toBe(true);

      ffm.disable('core_engine');
      expect(ffm.evaluate('ai_summarizer').enabled).toBe(false);
    });

    it('should enforce deterministic rollout percentage evaluation', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({
        featureName: 'canary_feature',
        enabled: true,
        rolloutPercentage: 50,
      });

      ffm.registerFeature(flag);

      const eval1 = ffm.evaluate('canary_feature', { userId: 'user_100' });
      const eval2 = ffm.evaluate('canary_feature', { userId: 'user_100' });

      expect(eval1.enabled).toBe(eval2.enabled);
    });

    it('should cache evaluation results and track cached evaluations telemetry', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({ featureName: 'cached_flag', enabled: true });

      ffm.registerFeature(flag);

      ffm.evaluate('cached_flag', { userId: 'u1' }); // Initial evaluation
      ffm.evaluate('cached_flag', { userId: 'u1' }); // Cache hit

      const stats = ffm.statistics();
      expect(stats.evaluations).toBe(2);
      expect(stats.cachedEvaluations).toBe(1);
    });

    it('should remove feature flag and invalidate evaluation cache', () => {
      const ffm = new FeatureFlagManager();
      const flag = createFeatureFlag({ featureName: 'to_remove', enabled: true });

      ffm.registerFeature(flag);
      expect(ffm.evaluate('to_remove').enabled).toBe(true);

      expect(ffm.removeFeature('to_remove')).toBe(true);
      expect(ffm.evaluate('to_remove').enabled).toBe(false);
    });

    it('should clear feature flags and evaluation cache', () => {
      const ffm = new FeatureFlagManager();
      ffm.registerFeature(createFeatureFlag({ featureName: 'f1', enabled: true }));
      expect(ffm.listFeatures().length).toBe(1);

      ffm.clear();
      expect(ffm.listFeatures().length).toBe(0);
    });

    it('should report feature flag health and statistics', () => {
      const ffm = new FeatureFlagManager();
      ffm.registerFeature(createFeatureFlag({ featureName: 'f1', enabled: true }));
      ffm.registerFeature(createFeatureFlag({ featureName: 'f2', enabled: false }));

      const health = ffm.health();
      expect(health.healthy).toBe(true);
      expect(health.totalFeatures).toBe(2);
      expect(health.enabledFeatures).toBe(1);
      expect(health.disabledFeatures).toBe(1);
    });
  });

  describe('4. Provider & Runtime Delegation Integration', () => {
    it('should override configuration values with active profile overrides', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', 500, { 'debug.enabled': true, 'other.key': 'val' }));

      expect(provider.get('debug.enabled')).toBe(false);
      expect(provider.get('other.key')).toBe('val');

      provider.activateProfile('development');
      expect(provider.get('debug.enabled')).toBe(true);
    });

    it('should delegate profile APIs through ConfigurationRuntime coordinator', () => {
      const runtime = new ConfigurationRuntime();
      const customProf = createConfigurationProfileDefinition({
        profileType: 'custom',
        profileName: 'custom_prof',
        overrides: { 'c.key': 99 },
      });

      runtime.registerProfile(customProf);
      expect(runtime.listProfiles().some((p) => p.profileName === 'custom_prof')).toBe(true);

      runtime.activateProfile('custom_prof');
      expect(runtime.getActiveProfile()?.profileName).toBe('custom_prof');
      expect(runtime.get('c.key')).toBe(99);

      const snapshot = runtime.createProfileSnapshot();
      expect(snapshot.activeProfileName).toBe('custom_prof');
    });

    it('should delegate feature flag APIs through ConfigurationRuntime coordinator', () => {
      const runtime = new ConfigurationRuntime();
      const flag = createFeatureFlag({ featureName: 'voice_ai', enabled: true });

      runtime.registerFeature(flag);
      expect(runtime.listFeatures().length).toBe(1);

      expect(runtime.evaluateFeature('voice_ai').enabled).toBe(true);

      runtime.toggleFeature('voice_ai');
      expect(runtime.evaluateFeature('voice_ai').enabled).toBe(false);

      expect(runtime.enableFeature('voice_ai'));
      expect(runtime.evaluateFeature('voice_ai').enabled).toBe(true);

      expect(runtime.disableFeature('voice_ai'));
      expect(runtime.evaluateFeature('voice_ai').enabled).toBe(false);

      expect(runtime.featureStatistics()).toBeDefined();
      expect(runtime.featureHealth().healthy).toBe(true);

      expect(runtime.removeFeature('voice_ai')).toBe(true);
      expect(runtime.listFeatures().length).toBe(0);
    });

    it('should include profile and feature telemetry in diagnostics()', () => {
      const provider = new ConfigurationProvider();
      provider.registerFeature(createFeatureFlag({ featureName: 'diag_flag', enabled: true }));
      provider.evaluateFeature('diag_flag');

      const diag = provider.diagnostics();
      expect(diag.activeProfile).toBe('production');
      expect(diag.profilesSnapshot).toBeDefined();
      expect(diag.profileStats).toBeDefined();
      expect(diag.featureStats).toBeDefined();
      expect(diag.featureHealth).toBeDefined();
    });
  });
});
