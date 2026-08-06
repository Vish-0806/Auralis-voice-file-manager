import { beforeEach, describe, expect, it } from 'vitest';
import {
  createFrontendCapabilities,
  createFrontendConfiguration,
  createFrontendContext,
  createFrontendDiagnostics,
  createFrontendHealth,
  createFrontendState,
  createFrontendStatistics,
  FrontendConfigurationException,
  FrontendInitializationException,
  FrontendProvider,
  FrontendProviderException,
  FrontendRuntime,
  FrontendRuntimeException,
  FrontendRuntimeState,
  FrontendValidationException,
  getFrontendProvider,
  getFrontendRuntime,
  resetFrontendProvider,
  resetFrontendRuntime,
  setFrontendProvider,
  setFrontendRuntime,
} from '../../src/runtime';

describe('Phase 16.1 — Frontend Runtime Foundation', () => {
  beforeEach(() => {
    resetFrontendRuntime();
    resetFrontendProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create default frozen state model', () => {
      const state = createFrontendState();
      expect(state.status).toBe(FrontendRuntimeState.UNINITIALIZED);
      expect(state.initialized).toBe(false);
      expect(state.startTime).toBeNull();
      expect(state.restartCount).toBe(0);
      expect(state.errorCount).toBe(0);
      expect(state.lastError).toBeNull();
      expect(Object.isFrozen(state)).toBe(true);
    });

    it('should create default frozen configuration model', () => {
      const config = createFrontendConfiguration();
      expect(config.appName).toBe('Auralis Frontend');
      expect(config.environment).toBe('production');
      expect(config.debug).toBe(false);
      expect(config.maxRetries).toBe(3);
      expect(config.timeoutMs).toBe(5000);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create default frozen capabilities model', () => {
      const caps = createFrontendCapabilities();
      expect(caps.offlineSupport).toBe(true);
      expect(caps.realTimeSync).toBe(true);
      expect(caps.storageQuotaMb).toBe(50);
      expect(caps.maxConcurrentOperations).toBe(10);
      expect(Object.isFrozen(caps)).toBe(true);
      expect(Object.isFrozen(caps.customFeatures)).toBe(true);
    });

    it('should create default frozen health model', () => {
      const health = createFrontendHealth();
      expect(health.healthy).toBe(false);
      expect(health.status).toBe(FrontendRuntimeState.UNINITIALIZED);
      expect(Object.isFrozen(health)).toBe(true);
      expect(Object.isFrozen(health.details)).toBe(true);
    });

    it('should create default frozen statistics model', () => {
      const stats = createFrontendStatistics();
      expect(stats.initializations).toBe(0);
      expect(stats.shutdowns).toBe(0);
      expect(stats.restarts).toBe(0);
      expect(stats.uptimeSeconds).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create default frozen context model', () => {
      const ctx = createFrontendContext();
      expect(ctx.appId).toBe('auralis-frontend');
      expect(ctx.environment).toBe('production');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create default frozen diagnostics model', () => {
      const diag = createFrontendDiagnostics();
      expect(diag.state).toBeDefined();
      expect(diag.health).toBeDefined();
      expect(diag.statistics).toBeDefined();
      expect(diag.capabilities).toBeDefined();
      expect(diag.context).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should accept custom values for configuration and keep model frozen', () => {
      const config = createFrontendConfiguration({
        appName: 'Custom App',
        debug: true,
      });
      expect(config.appName).toBe('Custom App');
      expect(config.debug).toBe(true);
      expect(Object.isFrozen(config)).toBe(true);
    });
  });

  describe('2. Exception Hierarchy', () => {
    it('should properly instantiate base FrontendRuntimeException', () => {
      const cause = new Error('Root cause');
      const err = new FrontendRuntimeException('Base runtime failure', cause);
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(FrontendRuntimeException);
      expect(err.name).toBe('FrontendRuntimeException');
      expect(err.message).toBe('Base runtime failure');
      expect(err.cause).toBe(cause);
    });

    it('should properly instantiate FrontendInitializationException', () => {
      const err = new FrontendInitializationException('Init error');
      expect(err).toBeInstanceOf(FrontendRuntimeException);
      expect(err).toBeInstanceOf(FrontendInitializationException);
      expect(err.name).toBe('FrontendInitializationException');
    });

    it('should properly instantiate FrontendConfigurationException', () => {
      const err = new FrontendConfigurationException('Config error');
      expect(err).toBeInstanceOf(FrontendRuntimeException);
      expect(err).toBeInstanceOf(FrontendConfigurationException);
      expect(err.name).toBe('FrontendConfigurationException');
    });

    it('should properly instantiate FrontendProviderException', () => {
      const err = new FrontendProviderException('Provider error');
      expect(err).toBeInstanceOf(FrontendRuntimeException);
      expect(err).toBeInstanceOf(FrontendProviderException);
      expect(err.name).toBe('FrontendProviderException');
    });

    it('should properly instantiate FrontendValidationException', () => {
      const err = new FrontendValidationException('Validation error');
      expect(err).toBeInstanceOf(FrontendRuntimeException);
      expect(err).toBeInstanceOf(FrontendValidationException);
      expect(err.name).toBe('FrontendValidationException');
    });
  });

  describe('3. FrontendProvider Operations', () => {
    it('should start in UNINITIALIZED state', () => {
      const provider = new FrontendProvider();
      expect(provider.status()).toBe(FrontendRuntimeState.UNINITIALIZED);
      expect(provider.state().initialized).toBe(false);
    });

    it('should initialize successfully and transition to READY', () => {
      const provider = new FrontendProvider();
      const health = provider.initialize();
      expect(provider.status()).toBe(FrontendRuntimeState.READY);
      expect(health.healthy).toBe(true);
      expect(health.status).toBe(FrontendRuntimeState.READY);
      expect(provider.state().initialized).toBe(true);
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should be idempotent on repeated initialize calls', () => {
      const provider = new FrontendProvider();
      provider.initialize();
      const health2 = provider.initialize();
      expect(health2.healthy).toBe(true);
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should shutdown successfully and transition to STOPPED', () => {
      const provider = new FrontendProvider();
      provider.initialize();
      const health = provider.shutdown();
      expect(provider.status()).toBe(FrontendRuntimeState.STOPPED);
      expect(health.healthy).toBe(false);
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should be idempotent on repeated shutdown calls', () => {
      const provider = new FrontendProvider();
      provider.initialize();
      provider.shutdown();
      provider.shutdown();
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should restart successfully', () => {
      const provider = new FrontendProvider();
      provider.initialize();
      const health = provider.restart();
      expect(provider.status()).toBe(FrontendRuntimeState.READY);
      expect(health.healthy).toBe(true);
      expect(provider.statistics().restarts).toBe(1);
      expect(provider.statistics().initializations).toBe(2);
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should provide complete diagnostics telemetry', () => {
      const provider = new FrontendProvider();
      provider.initialize();
      const diag = provider.diagnostics();
      expect(diag.state.status).toBe(FrontendRuntimeState.READY);
      expect(diag.health.healthy).toBe(true);
      expect(diag.statistics.initializations).toBe(1);
      expect(diag.capabilities.offlineSupport).toBe(true);
      expect(diag.context.appId).toBe('auralis-frontend');
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should accept custom configuration via constructor injection', () => {
      const customConfig = createFrontendConfiguration({ appName: 'Injected App' });
      const provider = new FrontendProvider(customConfig);
      expect(provider.configuration().appName).toBe('Injected App');
    });

    it('should accept custom capabilities via constructor injection', () => {
      const customCaps = createFrontendCapabilities({ storageQuotaMb: 100 });
      const provider = new FrontendProvider(undefined, customCaps);
      expect(provider.capabilities().storageQuotaMb).toBe(100);
    });
  });

  describe('4. FrontendRuntime & Provider Delegation', () => {
    it('should instantiate runtime with default provider if not supplied', () => {
      const runtime = new FrontendRuntime();
      expect(runtime.provider()).toBeDefined();
      expect(runtime.status()).toBe(FrontendRuntimeState.UNINITIALIZED);
    });

    it('should delegate lifecycle methods to injected provider', () => {
      const provider = new FrontendProvider();
      const runtime = new FrontendRuntime(provider);

      expect(runtime.status()).toBe(FrontendRuntimeState.UNINITIALIZED);

      const healthInit = runtime.initialize();
      expect(healthInit.healthy).toBe(true);
      expect(runtime.status()).toBe(FrontendRuntimeState.READY);

      const stats = runtime.statistics();
      expect(stats.initializations).toBe(1);

      const caps = runtime.capabilities();
      expect(caps.offlineSupport).toBe(true);

      const diag = runtime.diagnostics();
      expect(diag.health.healthy).toBe(true);

      const healthShutdown = runtime.shutdown();
      expect(healthShutdown.healthy).toBe(false);
      expect(runtime.status()).toBe(FrontendRuntimeState.STOPPED);
    });

    it('should delegate restart to injected provider', () => {
      const provider = new FrontendProvider();
      const runtime = new FrontendRuntime(provider);
      runtime.initialize();

      const healthRestart = runtime.restart();
      expect(healthRestart.healthy).toBe(true);
      expect(runtime.statistics().restarts).toBe(1);
    });
  });

  describe('5. Singleton Helpers', () => {
    it('should lazily create global provider singleton', () => {
      const provider1 = getFrontendProvider();
      const provider2 = getFrontendProvider();
      expect(provider1).toBe(provider2);
    });

    it('should allow setting custom global provider', () => {
      const customProvider = new FrontendProvider();
      setFrontendProvider(customProvider);
      expect(getFrontendProvider()).toBe(customProvider);
    });

    it('should reset global provider singleton', () => {
      const provider1 = getFrontendProvider();
      resetFrontendProvider();
      const provider2 = getFrontendProvider();
      expect(provider1).not.toBe(provider2);
    });

    it('should lazily create global runtime singleton using global provider', () => {
      const runtime1 = getFrontendRuntime();
      const runtime2 = getFrontendRuntime();
      expect(runtime1).toBe(runtime2);
      expect(runtime1.provider()).toBe(getFrontendProvider());
    });

    it('should allow setting custom global runtime', () => {
      const customRuntime = new FrontendRuntime();
      setFrontendRuntime(customRuntime);
      expect(getFrontendRuntime()).toBe(customRuntime);
    });

    it('should reset global runtime singleton', () => {
      const runtime1 = getFrontendRuntime();
      resetFrontendRuntime();
      const runtime2 = getFrontendRuntime();
      expect(runtime1).not.toBe(runtime2);
    });

    it('should handle concurrent-safe singleton resets cleanly', () => {
      const r1 = getFrontendRuntime();
      setFrontendRuntime(r1);
      resetFrontendRuntime();
      resetFrontendProvider();
      const r2 = getFrontendRuntime();
      expect(r1).not.toBe(r2);
    });
  });
});
