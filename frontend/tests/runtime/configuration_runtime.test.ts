import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationConfigurationException,
  ConfigurationInitializationException,
  ConfigurationProvider,
  ConfigurationProviderException,
  ConfigurationRuntime,
  ConfigurationRuntimeException,
  ConfigurationRuntimeState,
  ConfigurationValidationException,
  createConfigurationCapabilities,
  createConfigurationConfiguration,
  createConfigurationContext,
  createConfigurationDiagnostics,
  createConfigurationHealth,
  createConfigurationState,
  createConfigurationStatistics,
  getConfigurationProvider,
  getConfigurationRuntime,
  resetConfigurationProvider,
  resetConfigurationRuntime,
  setConfigurationProvider,
  setConfigurationRuntime,
} from '../../src/runtime/config';

describe('Phase 16.3.1 — Frontend Configuration Runtime Foundation', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. Enum Values', () => {
    it('should verify ConfigurationRuntimeState enum UNINITIALIZED', () => {
      expect(ConfigurationRuntimeState.UNINITIALIZED).toBe('UNINITIALIZED');
    });

    it('should verify ConfigurationRuntimeState enum INITIALIZING', () => {
      expect(ConfigurationRuntimeState.INITIALIZING).toBe('INITIALIZING');
    });

    it('should verify ConfigurationRuntimeState enum READY', () => {
      expect(ConfigurationRuntimeState.READY).toBe('READY');
    });

    it('should verify ConfigurationRuntimeState enum STOPPING', () => {
      expect(ConfigurationRuntimeState.STOPPING).toBe('STOPPING');
    });

    it('should verify ConfigurationRuntimeState enum STOPPED', () => {
      expect(ConfigurationRuntimeState.STOPPED).toBe('STOPPED');
    });
  });

  describe('2. Immutable Models & Factory Functions', () => {
    it('should create immutable ConfigurationState with default values', () => {
      const defaultState = createConfigurationState();
      expect(defaultState.runtimeState).toBe(ConfigurationRuntimeState.UNINITIALIZED);
      expect(defaultState.initialized).toBe(false);
      expect(defaultState.startedAt).toBeNull();
      expect(Object.isFrozen(defaultState)).toBe(true);
    });

    it('should create immutable ConfigurationState with custom overrides', () => {
      const customState = createConfigurationState({
        runtimeState: ConfigurationRuntimeState.READY,
        initialized: true,
        startedAt: '2026-01-01T00:00:00.000Z',
      });
      expect(customState.runtimeState).toBe(ConfigurationRuntimeState.READY);
      expect(customState.initialized).toBe(true);
      expect(customState.startedAt).toBe('2026-01-01T00:00:00.000Z');
      expect(Object.isFrozen(customState)).toBe(true);
    });

    it('should create immutable ConfigurationCapabilities with default flags', () => {
      const caps = createConfigurationCapabilities();
      expect(caps.supportsProfiles).toBe(true);
      expect(caps.supportsSources).toBe(true);
      expect(caps.supportsValidation).toBe(true);
      expect(caps.supportsSecrets).toBe(true);
      expect(caps.supportsFeatureFlags).toBe(true);
      expect(caps.supportsDiagnostics).toBe(true);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create immutable ConfigurationCapabilities with overridden flags', () => {
      const caps = createConfigurationCapabilities({ supportsSecrets: false, supportsProfiles: false });
      expect(caps.supportsSecrets).toBe(false);
      expect(caps.supportsProfiles).toBe(false);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create immutable ConfigurationHealth evaluation snapshot', () => {
      const health = createConfigurationHealth({ healthy: true, message: 'Ready' });
      expect(health.healthy).toBe(true);
      expect(health.message).toBe('Ready');
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable ConfigurationStatistics metrics model', () => {
      const stats = createConfigurationStatistics({ initializations: 2, shutdowns: 1 });
      expect(stats.initializations).toBe(2);
      expect(stats.shutdowns).toBe(1);
      expect(stats.uptime).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable ConfigurationContext metadata model', () => {
      const ctx = createConfigurationContext({ runtimeId: 'rt_100', environment: 'staging' });
      expect(ctx.runtimeId).toBe('rt_100');
      expect(ctx.environment).toBe('staging');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create immutable ConfigurationConfiguration settings model', () => {
      const cfg = createConfigurationConfiguration({ runtimeName: 'Custom Runtime', strictMode: false });
      expect(cfg.runtimeName).toBe('Custom Runtime');
      expect(cfg.strictMode).toBe(false);
      expect(cfg.version).toBe('1.0.0');
      expect(Object.isFrozen(cfg)).toBe(true);
    });

    it('should create immutable ConfigurationDiagnostics snapshot', () => {
      const diag = createConfigurationDiagnostics();
      expect(diag.health).toBeDefined();
      expect(diag.statistics).toBeDefined();
      expect(diag.capabilities).toBeDefined();
      expect(diag.context).toBeDefined();
      expect(diag.timestamp).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('3. Exception Hierarchy', () => {
    it('should verify ConfigurationRuntimeException base class', () => {
      const baseErr = new ConfigurationRuntimeException('Base error');
      expect(baseErr).toBeInstanceOf(Error);
      expect(baseErr).toBeInstanceOf(ConfigurationRuntimeException);
      expect(baseErr.name).toBe('ConfigurationRuntimeException');
      expect(baseErr.message).toBe('Base error');
    });

    it('should verify ConfigurationInitializationException subclass', () => {
      const initErr = new ConfigurationInitializationException('Init error');
      expect(initErr).toBeInstanceOf(ConfigurationRuntimeException);
      expect(initErr).toBeInstanceOf(ConfigurationInitializationException);
      expect(initErr.name).toBe('ConfigurationInitializationException');
    });

    it('should verify ConfigurationProviderException subclass', () => {
      const provErr = new ConfigurationProviderException('Provider error');
      expect(provErr).toBeInstanceOf(ConfigurationRuntimeException);
      expect(provErr).toBeInstanceOf(ConfigurationProviderException);
      expect(provErr.name).toBe('ConfigurationProviderException');
    });

    it('should verify ConfigurationValidationException subclass', () => {
      const valErr = new ConfigurationValidationException('Val error');
      expect(valErr).toBeInstanceOf(ConfigurationRuntimeException);
      expect(valErr).toBeInstanceOf(ConfigurationValidationException);
      expect(valErr.name).toBe('ConfigurationValidationException');
    });

    it('should verify ConfigurationConfigurationException subclass', () => {
      const cfgErr = new ConfigurationConfigurationException('Cfg error');
      expect(cfgErr).toBeInstanceOf(ConfigurationRuntimeException);
      expect(cfgErr).toBeInstanceOf(ConfigurationConfigurationException);
      expect(cfgErr.name).toBe('ConfigurationConfigurationException');
    });
  });

  describe('4. ConfigurationProvider Lifecycle & Operations', () => {
    it('should initialize uninitialized provider and set startedAt', () => {
      const provider = new ConfigurationProvider();
      expect(provider.state().runtimeState).toBe(ConfigurationRuntimeState.UNINITIALIZED);
      expect(provider.state().initialized).toBe(false);

      const health = provider.initialize();
      expect(health.healthy).toBe(true);
      expect(provider.state().runtimeState).toBe(ConfigurationRuntimeState.READY);
      expect(provider.state().initialized).toBe(true);
      expect(provider.state().startedAt).not.toBeNull();
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should handle idempotent initialization calls without double counting', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      const secondHealth = provider.initialize();

      expect(secondHealth.healthy).toBe(true);
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should shutdown operational provider and reset startedAt', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      expect(provider.state().initialized).toBe(true);

      const health = provider.shutdown();
      expect(health.healthy).toBe(false);
      expect(provider.state().runtimeState).toBe(ConfigurationRuntimeState.STOPPED);
      expect(provider.state().initialized).toBe(false);
      expect(provider.state().startedAt).toBeNull();
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should handle idempotent shutdown calls without double counting', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      provider.shutdown();
      const secondShutdown = provider.shutdown();

      expect(secondShutdown.healthy).toBe(false);
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should restart provider cleanly and update restart statistics', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      const health = provider.restart();

      expect(health.healthy).toBe(true);
      expect(provider.state().runtimeState).toBe(ConfigurationRuntimeState.READY);
      expect(provider.statistics().restarts).toBe(1);
      expect(provider.statistics().initializations).toBe(2);
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should evaluate health snapshot correctly based on state', () => {
      const provider = new ConfigurationProvider();
      expect(provider.health().healthy).toBe(false);
      provider.initialize();
      expect(provider.health().healthy).toBe(true);
    });

    it('should produce diagnostics snapshot', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      const diag = provider.diagnostics();

      expect(diag.health.healthy).toBe(true);
      expect(diag.statistics.initializations).toBe(1);
      expect(diag.capabilities.supportsDiagnostics).toBe(true);
    });
  });

  describe('5. ConfigurationRuntime Coordinator', () => {
    it('should delegate initialize lifecycle method to underlying provider', () => {
      const provider = new ConfigurationProvider();
      const runtime = new ConfigurationRuntime(provider);

      const initHealth = runtime.initialize();
      expect(initHealth.healthy).toBe(true);
      expect(runtime.state().runtimeState).toBe(ConfigurationRuntimeState.READY);
    });

    it('should delegate restart lifecycle method to underlying provider', () => {
      const provider = new ConfigurationProvider();
      const runtime = new ConfigurationRuntime(provider);
      runtime.initialize();

      const restartHealth = runtime.restart();
      expect(restartHealth.healthy).toBe(true);
      expect(runtime.statistics().restarts).toBe(1);
    });

    it('should delegate shutdown lifecycle method to underlying provider', () => {
      const provider = new ConfigurationProvider();
      const runtime = new ConfigurationRuntime(provider);
      runtime.initialize();

      const shutdownHealth = runtime.shutdown();
      expect(shutdownHealth.healthy).toBe(false);
      expect(runtime.state().runtimeState).toBe(ConfigurationRuntimeState.STOPPED);
    });

    it('should expose provider instance via provider() accessor', () => {
      const provider = new ConfigurationProvider();
      const runtime = new ConfigurationRuntime(provider);
      expect(runtime.provider()).toBe(provider);
    });

    it('should expose health, statistics, and diagnostics delegation', () => {
      const runtime = new ConfigurationRuntime();
      runtime.initialize();

      expect(runtime.health().healthy).toBe(true);
      expect(runtime.statistics().initializations).toBe(1);
      expect(runtime.diagnostics().timestamp).toBeDefined();
    });
  });

  describe('6. Singleton Accessors & Helpers', () => {
    it('should lazily instantiate singleton ConfigurationProvider', () => {
      const provider1 = getConfigurationProvider();
      const provider2 = getConfigurationProvider();
      expect(provider1).toBe(provider2);
    });

    it('should lazily instantiate singleton ConfigurationRuntime', () => {
      const runtime1 = getConfigurationRuntime();
      const runtime2 = getConfigurationRuntime();
      expect(runtime1).toBe(runtime2);
    });

    it('should allow setting custom singleton provider and resetting instance', () => {
      const customProvider = new ConfigurationProvider();
      setConfigurationProvider(customProvider);
      expect(getConfigurationProvider()).toBe(customProvider);

      resetConfigurationProvider();
      expect(getConfigurationProvider()).not.toBe(customProvider);
    });

    it('should allow setting custom singleton runtime and resetting instance', () => {
      const customRuntime = new ConfigurationRuntime();
      setConfigurationRuntime(customRuntime);
      expect(getConfigurationRuntime()).toBe(customRuntime);

      resetConfigurationRuntime();
      expect(getConfigurationRuntime()).not.toBe(customRuntime);
    });
  });

  describe('7. Constructor Dependency Injection & Instance Isolation', () => {
    it('should accept custom configuration, capabilities, and context in provider constructor', () => {
      const customCfg = createConfigurationConfiguration({ runtimeName: 'AppConfig' });
      const customCaps = createConfigurationCapabilities({ supportsSecrets: false });
      const customCtx = createConfigurationContext({ environment: 'test' });

      const provider = new ConfigurationProvider(customCfg, customCaps, customCtx);

      expect(provider.configuration().runtimeName).toBe('AppConfig');
      expect(provider.capabilities().supportsSecrets).toBe(false);
      expect(provider.context().environment).toBe('test');
    });

    it('should isolate state between multiple runtime instances', () => {
      const runtime1 = new ConfigurationRuntime();
      const runtime2 = new ConfigurationRuntime();

      runtime1.initialize();

      expect(runtime1.state().runtimeState).toBe(ConfigurationRuntimeState.READY);
      expect(runtime2.state().runtimeState).toBe(ConfigurationRuntimeState.UNINITIALIZED);
    });
  });
});
