import { beforeEach, describe, expect, it } from 'vitest';
import {
  CommandExecutionException,
  CommandInitializationException,
  CommandProvider,
  CommandProviderException,
  CommandRuntime,
  CommandRuntimeException,
  CommandRuntimeState,
  CommandValidationException,
  createCommandCapabilities,
  createCommandConfiguration,
  createCommandContext,
  createCommandDiagnostics,
  createCommandHealth,
  createCommandState,
  createCommandStatistics,
  getCommandProvider,
  getCommandRuntime,
  resetCommandProvider,
  resetCommandRuntime,
  setCommandProvider,
  setCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.1 — Frontend Command Runtime Foundation', () => {
  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();
  });

  describe('1. CommandRuntimeState Enum', () => {
    it('should verify CommandRuntimeState values', () => {
      expect(CommandRuntimeState.UNINITIALIZED).toBe('UNINITIALIZED');
      expect(CommandRuntimeState.INITIALIZING).toBe('INITIALIZING');
      expect(CommandRuntimeState.READY).toBe('READY');
      expect(CommandRuntimeState.STOPPING).toBe('STOPPING');
      expect(CommandRuntimeState.STOPPED).toBe('STOPPED');
    });
  });

  describe('2. Immutable Domain Models & Factory Functions', () => {
    it('should create immutable CommandState model with default parameters', () => {
      const state = createCommandState();
      expect(state.runtimeState).toBe(CommandRuntimeState.UNINITIALIZED);
      expect(state.initialized).toBe(false);
      expect(state.startedAt).toBeNull();
      expect(Object.isFrozen(state)).toBe(true);
    });

    it('should create immutable CommandState model with custom parameters', () => {
      const ts = new Date().toISOString();
      const state = createCommandState({
        runtimeState: CommandRuntimeState.READY,
        initialized: true,
        startedAt: ts,
      });

      expect(state.runtimeState).toBe(CommandRuntimeState.READY);
      expect(state.initialized).toBe(true);
      expect(state.startedAt).toBe(ts);
      expect(Object.isFrozen(state)).toBe(true);
    });

    it('should create immutable CommandContext model', () => {
      const ctx = createCommandContext({ environment: 'testing', runtimeId: 'rt_custom' });
      expect(ctx.environment).toBe('testing');
      expect(ctx.runtimeId).toBe('rt_custom');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create CommandContext with default values', () => {
      const ctx = createCommandContext();
      expect(ctx.environment).toBe('production');
      expect(ctx.runtimeId).toBeDefined();
      expect(ctx.createdAt).toBeDefined();
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create immutable CommandCapabilities model', () => {
      const cap = createCommandCapabilities({ supportsUndoRedo: false });
      expect(cap.supportsCommandExecution).toBe(true);
      expect(cap.supportsCommandValidation).toBe(true);
      expect(cap.supportsUndoRedo).toBe(false);
      expect(cap.supportsCommandHistory).toBe(true);
      expect(cap.supportsBatchExecution).toBe(true);
      expect(cap.supportsDiagnostics).toBe(true);
      expect(Object.isFrozen(cap)).toBe(true);
    });

    it('should create immutable CommandStatistics model', () => {
      const stats = createCommandStatistics({ initializations: 2, restarts: 1, uptime: 100 });
      expect(stats.initializations).toBe(2);
      expect(stats.restarts).toBe(1);
      expect(stats.uptime).toBe(100);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create CommandStatistics with default zero values', () => {
      const stats = createCommandStatistics();
      expect(stats.initializations).toBe(0);
      expect(stats.shutdowns).toBe(0);
      expect(stats.restarts).toBe(0);
      expect(stats.errors).toBe(0);
      expect(stats.uptime).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable CommandHealth model', () => {
      const health = createCommandHealth({
        healthy: true,
        runtimeState: CommandRuntimeState.READY,
        message: 'OK',
      });
      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(CommandRuntimeState.READY);
      expect(health.message).toBe('OK');
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create CommandHealth with default unhealthy state', () => {
      const health = createCommandHealth();
      expect(health.healthy).toBe(false);
      expect(health.runtimeState).toBe(CommandRuntimeState.UNINITIALIZED);
      expect(health.message).toBe('Command runtime is uninitialized.');
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable CommandConfiguration model', () => {
      const config = createCommandConfiguration({
        runtimeName: 'Custom Command Engine',
        maxHistorySize: 500,
      });
      expect(config.runtimeName).toBe('Custom Command Engine');
      expect(config.maxHistorySize).toBe(500);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create CommandConfiguration with default values', () => {
      const config = createCommandConfiguration();
      expect(config.runtimeName).toBe('Auralis Command Runtime');
      expect(config.version).toBe('1.0.0');
      expect(config.strictMode).toBe(true);
      expect(config.maxHistorySize).toBe(1000);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create immutable CommandDiagnostics model', () => {
      const diag = createCommandDiagnostics();
      expect(diag.health).toBeDefined();
      expect(diag.statistics).toBeDefined();
      expect(diag.capabilities).toBeDefined();
      expect(diag.context).toBeDefined();
      expect(diag.timestamp).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should create CommandDiagnostics with custom nested models', () => {
      const health = createCommandHealth({ healthy: true, runtimeState: CommandRuntimeState.READY });
      const stats = createCommandStatistics({ initializations: 3 });
      const diag = createCommandDiagnostics({ health, statistics: stats });

      expect(diag.health.healthy).toBe(true);
      expect(diag.statistics.initializations).toBe(3);
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('3. Exception Hierarchy', () => {
    it('should instantiate CommandRuntimeException as base Error subclass', () => {
      const err = new CommandRuntimeException('Runtime failure');
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(CommandRuntimeException);
      expect(err.name).toBe('CommandRuntimeException');
      expect(err.message).toBe('Runtime failure');
    });

    it('should instantiate CommandInitializationException', () => {
      const err = new CommandInitializationException('Init failed');
      expect(err).toBeInstanceOf(CommandRuntimeException);
      expect(err).toBeInstanceOf(Error);
      expect(err.name).toBe('CommandInitializationException');
      expect(err.message).toBe('Init failed');
    });

    it('should instantiate CommandProviderException', () => {
      const err = new CommandProviderException('Provider failed');
      expect(err).toBeInstanceOf(CommandRuntimeException);
      expect(err.name).toBe('CommandProviderException');
      expect(err.message).toBe('Provider failed');
    });

    it('should instantiate CommandExecutionException', () => {
      const err = new CommandExecutionException('Execution failed');
      expect(err).toBeInstanceOf(CommandRuntimeException);
      expect(err.name).toBe('CommandExecutionException');
      expect(err.message).toBe('Execution failed');
    });

    it('should instantiate CommandValidationException', () => {
      const err = new CommandValidationException('Validation failed');
      expect(err).toBeInstanceOf(CommandRuntimeException);
      expect(err.name).toBe('CommandValidationException');
      expect(err.message).toBe('Validation failed');
    });

    it('should preserve stack traces across exception hierarchy', () => {
      const err = new CommandExecutionException('stack test');
      expect(err.stack).toBeDefined();
      expect(err.stack).toContain('stack test');
    });
  });

  describe('4. CommandProvider Engine & Lifecycle Transitions', () => {
    it('should start in UNINITIALIZED state', () => {
      const provider = new CommandProvider();
      const state = provider.state();
      expect(state.runtimeState).toBe(CommandRuntimeState.UNINITIALIZED);
      expect(state.initialized).toBe(false);

      const health = provider.health();
      expect(health.healthy).toBe(false);
    });

    it('should accept custom configuration, capabilities, and context in constructor', () => {
      const cfg = createCommandConfiguration({ runtimeName: 'CustomApp' });
      const cap = createCommandCapabilities({ supportsUndoRedo: false });
      const ctx = createCommandContext({ environment: 'staging' });

      const provider = new CommandProvider(cfg, cap, ctx);
      expect(provider.configuration().runtimeName).toBe('CustomApp');
      expect(provider.capabilities().supportsUndoRedo).toBe(false);
      expect(provider.context().environment).toBe('staging');
    });

    it('should transition to READY on initialize()', () => {
      const provider = new CommandProvider();
      const health = provider.initialize();

      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(CommandRuntimeState.READY);

      const state = provider.state();
      expect(state.runtimeState).toBe(CommandRuntimeState.READY);
      expect(state.initialized).toBe(true);
      expect(state.startedAt).toBeDefined();
    });

    it('should handle idempotent initialize() calls without incrementing statistics', () => {
      const provider = new CommandProvider();
      provider.initialize();
      const h2 = provider.initialize();

      expect(h2.healthy).toBe(true);
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should transition to STOPPED on shutdown()', () => {
      const provider = new CommandProvider();
      provider.initialize();

      const health = provider.shutdown();
      expect(health.healthy).toBe(false);
      expect(health.runtimeState).toBe(CommandRuntimeState.STOPPED);

      const state = provider.state();
      expect(state.runtimeState).toBe(CommandRuntimeState.STOPPED);
      expect(state.initialized).toBe(false);
      expect(state.startedAt).toBeNull();
    });

    it('should handle idempotent shutdown() calls when already STOPPED', () => {
      const provider = new CommandProvider();
      provider.initialize();
      provider.shutdown();
      const h2 = provider.shutdown();

      expect(h2.healthy).toBe(false);
      expect(provider.statistics().shutdowns).toBe(1);
    });

    it('should handle restart() transition by shutting down and re-initializing', () => {
      const provider = new CommandProvider();
      provider.initialize();

      const health = provider.restart();
      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(CommandRuntimeState.READY);

      const stats = provider.statistics();
      expect(stats.restarts).toBe(1);
      expect(stats.initializations).toBe(2);
      expect(stats.shutdowns).toBe(1);
    });

    it('should correctly report status()', () => {
      const provider = new CommandProvider();
      expect(provider.status()).toBe(CommandRuntimeState.UNINITIALIZED);

      provider.initialize();
      expect(provider.status()).toBe(CommandRuntimeState.READY);

      provider.shutdown();
      expect(provider.status()).toBe(CommandRuntimeState.STOPPED);
    });

    it('should produce diagnostics snapshot containing health, stats, and capabilities', () => {
      const provider = new CommandProvider();
      provider.initialize();

      const diag = provider.diagnostics();
      expect(diag.health.healthy).toBe(true);
      expect(diag.statistics.initializations).toBe(1);
      expect(diag.capabilities.supportsCommandExecution).toBe(true);
      expect(diag.context.environment).toBe('production');
      expect(diag.timestamp).toBeDefined();
    });

    it('should report zero uptime when not initialized', () => {
      const provider = new CommandProvider();
      expect(provider.statistics().uptime).toBe(0);
    });

    it('should report zero uptime after shutdown', () => {
      const provider = new CommandProvider();
      provider.initialize();
      provider.shutdown();
      expect(provider.statistics().uptime).toBe(0);
    });

    it('should track health message based on runtime state', () => {
      const provider = new CommandProvider();

      const h1 = provider.health();
      expect(h1.message).toContain('UNINITIALIZED');

      provider.initialize();
      const h2 = provider.health();
      expect(h2.message).toBe('Command runtime is ready and operational.');

      provider.shutdown();
      const h3 = provider.health();
      expect(h3.message).toContain('STOPPED');
    });

    it('should allow multiple restart cycles', () => {
      const provider = new CommandProvider();
      provider.initialize();
      provider.restart();
      provider.restart();
      provider.restart();

      const stats = provider.statistics();
      expect(stats.restarts).toBe(3);
      expect(stats.initializations).toBe(4);
      expect(stats.shutdowns).toBe(3);
      expect(provider.health().healthy).toBe(true);
    });
  });

  describe('5. CommandRuntime Coordinator & Delegation', () => {
    it('should delegate lifecycle methods to injected provider', () => {
      const provider = new CommandProvider();
      const runtime = new CommandRuntime(provider);

      expect(runtime.state().runtimeState).toBe(CommandRuntimeState.UNINITIALIZED);

      const h1 = runtime.initialize();
      expect(h1.healthy).toBe(true);
      expect(runtime.health().healthy).toBe(true);

      const h2 = runtime.shutdown();
      expect(h2.healthy).toBe(false);
      expect(runtime.state().runtimeState).toBe(CommandRuntimeState.STOPPED);
    });

    it('should return provider reference via provider()', () => {
      const provider = new CommandProvider();
      const runtime = new CommandRuntime(provider);
      expect(runtime.provider()).toBe(provider);
    });

    it('should delegate statistics, capabilities, and diagnostics', () => {
      const provider = new CommandProvider();
      const runtime = new CommandRuntime(provider);
      runtime.initialize();

      expect(runtime.statistics().initializations).toBe(1);
      expect(runtime.capabilities().supportsCommandExecution).toBe(true);
      expect(runtime.diagnostics().health.healthy).toBe(true);
    });

    it('should delegate restart() method through CommandRuntime', () => {
      const runtime = new CommandRuntime();
      runtime.initialize();
      const health = runtime.restart();

      expect(health.healthy).toBe(true);
      expect(runtime.statistics().restarts).toBe(1);
    });

    it('should delegate status() to provider', () => {
      const runtime = new CommandRuntime();
      expect(runtime.status()).toBe(CommandRuntimeState.UNINITIALIZED);

      runtime.initialize();
      expect(runtime.status()).toBe(CommandRuntimeState.READY);
    });

    it('should create default provider when none injected', () => {
      const runtime = new CommandRuntime();
      expect(runtime.provider()).toBeDefined();
      expect(runtime.state().runtimeState).toBe(CommandRuntimeState.UNINITIALIZED);
    });

    it('should delegate state() to provider', () => {
      const provider = new CommandProvider();
      const runtime = new CommandRuntime(provider);

      runtime.initialize();
      const state = runtime.state();
      expect(state.initialized).toBe(true);
      expect(state.runtimeState).toBe(CommandRuntimeState.READY);
      expect(state.startedAt).toBeDefined();
    });
  });

  describe('6. Lazy Singleton Helpers', () => {
    it('should lazily instantiate global provider and runtime', () => {
      const p1 = getCommandProvider();
      const p2 = getCommandProvider();
      expect(p1).toBe(p2);

      const r1 = getCommandRuntime();
      const r2 = getCommandRuntime();
      expect(r1).toBe(r2);
      expect(r1.provider()).toBe(p1);
    });

    it('should allow setting custom provider and runtime', () => {
      const customP = new CommandProvider();
      setCommandProvider(customP);
      expect(getCommandProvider()).toBe(customP);

      const customR = new CommandRuntime(customP);
      setCommandRuntime(customR);
      expect(getCommandRuntime()).toBe(customR);
    });

    it('should reset singleton instances cleanly via resetCommandRuntime()', () => {
      const r1 = getCommandRuntime();
      r1.initialize();
      expect(r1.health().healthy).toBe(true);

      resetCommandRuntime();

      const r2 = getCommandRuntime();
      expect(r2).not.toBe(r1);
      expect(r2.health().healthy).toBe(false);
    });

    it('should reset command provider cleanly via resetCommandProvider()', () => {
      const p1 = getCommandProvider();
      p1.initialize();
      expect(p1.health().healthy).toBe(true);

      resetCommandProvider();

      const p2 = getCommandProvider();
      expect(p2).not.toBe(p1);
      expect(p2.health().healthy).toBe(false);
    });

    it('should cascade resetCommandRuntime to also reset provider', () => {
      const p1 = getCommandProvider();
      const r1 = getCommandRuntime();
      r1.initialize();

      resetCommandRuntime();

      const p2 = getCommandProvider();
      expect(p2).not.toBe(p1);
    });

    it('should create new runtime with fresh provider after reset', () => {
      const r1 = getCommandRuntime();
      r1.initialize();
      expect(r1.statistics().initializations).toBe(1);

      resetCommandRuntime();

      const r2 = getCommandRuntime();
      r2.initialize();
      expect(r2.statistics().initializations).toBe(1);
    });
  });
});
