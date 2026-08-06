import { beforeEach, describe, expect, it } from 'vitest';
import {
  createEventCapabilities,
  createEventConfiguration,
  createEventContext,
  createEventDiagnostics,
  createEventHealth,
  createEventState,
  createEventStatistics,
  createFrontendEvent,
  EventDispatchException,
  EventInitializationException,
  EventPriority,
  EventProvider,
  EventProviderException,
  EventRuntime,
  EventRuntimeException,
  EventRuntimeState,
  EventValidationException,
  getEventProvider,
  getEventRuntime,
  resetEventProvider,
  resetEventRuntime,
  setEventProvider,
  setEventRuntime,
} from '../../src/runtime/events';

describe('Phase 16.4.1 — Frontend Event & Messaging Runtime Foundation', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Enums & Priority Values', () => {
    it('should verify EventRuntimeState values', () => {
      expect(EventRuntimeState.UNINITIALIZED).toBe('UNINITIALIZED');
      expect(EventRuntimeState.INITIALIZING).toBe('INITIALIZING');
      expect(EventRuntimeState.READY).toBe('READY');
      expect(EventRuntimeState.STOPPING).toBe('STOPPING');
      expect(EventRuntimeState.STOPPED).toBe('STOPPED');
    });

    it('should verify EventPriority numeric order', () => {
      expect(EventPriority.LOW).toBe(0);
      expect(EventPriority.NORMAL).toBe(100);
      expect(EventPriority.HIGH).toBe(200);
      expect(EventPriority.CRITICAL).toBe(300);
      expect(EventPriority.CRITICAL).toBeGreaterThan(EventPriority.HIGH);
    });
  });

  describe('2. Immutable Domain Models & Factory Functions', () => {
    it('should create immutable EventState model with default parameters', () => {
      const state = createEventState();
      expect(state.runtimeState).toBe(EventRuntimeState.UNINITIALIZED);
      expect(state.initialized).toBe(false);
      expect(state.startedAt).toBeNull();
      expect(Object.isFrozen(state)).toBe(true);
    });

    it('should create immutable EventState model with custom parameters', () => {
      const ts = new Date().toISOString();
      const state = createEventState({
        runtimeState: EventRuntimeState.READY,
        initialized: true,
        startedAt: ts,
      });

      expect(state.runtimeState).toBe(EventRuntimeState.READY);
      expect(state.initialized).toBe(true);
      expect(state.startedAt).toBe(ts);
      expect(Object.isFrozen(state)).toBe(true);
    });

    it('should create immutable FrontendEvent model', () => {
      const event = createFrontendEvent({
        eventType: 'user.created',
        payload: { userId: '123' },
        priority: EventPriority.HIGH,
        source: 'UserComponent',
        correlationId: 'corr_99',
      });

      expect(event.eventType).toBe('user.created');
      expect(event.payload).toEqual({ userId: '123' });
      expect(event.priority).toBe(EventPriority.HIGH);
      expect(event.source).toBe('UserComponent');
      expect(event.correlationId).toBe('corr_99');
      expect(event.eventId).toBeDefined();
      expect(event.timestamp).toBeDefined();
      expect(Object.isFrozen(event)).toBe(true);
    });

    it('should create immutable EventContext model', () => {
      const ctx = createEventContext({ environment: 'testing', runtimeId: 'rt_custom' });
      expect(ctx.environment).toBe('testing');
      expect(ctx.runtimeId).toBe('rt_custom');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create immutable EventCapabilities model', () => {
      const cap = createEventCapabilities({ supportsDeadLetterQueue: false });
      expect(cap.supportsEventBus).toBe(true);
      expect(cap.supportsPubSub).toBe(true);
      expect(cap.supportsAsyncDispatch).toBe(true);
      expect(cap.supportsFiltering).toBe(true);
      expect(cap.supportsDeadLetterQueue).toBe(false);
      expect(cap.supportsDiagnostics).toBe(true);
      expect(Object.isFrozen(cap)).toBe(true);
    });

    it('should create immutable EventStatistics model', () => {
      const stats = createEventStatistics({ initializations: 2, restarts: 1, uptime: 100 });
      expect(stats.initializations).toBe(2);
      expect(stats.restarts).toBe(1);
      expect(stats.uptime).toBe(100);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable EventHealth model', () => {
      const health = createEventHealth({ healthy: true, runtimeState: EventRuntimeState.READY, message: 'OK' });
      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(EventRuntimeState.READY);
      expect(health.message).toBe('OK');
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable EventConfiguration model', () => {
      const config = createEventConfiguration({ runtimeName: 'Custom Event Engine', maxQueueSize: 500 });
      expect(config.runtimeName).toBe('Custom Event Engine');
      expect(config.maxQueueSize).toBe(500);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create immutable EventDiagnostics model', () => {
      const diag = createEventDiagnostics();
      expect(diag.health).toBeDefined();
      expect(diag.statistics).toBeDefined();
      expect(diag.capabilities).toBeDefined();
      expect(diag.context).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('3. Exception Hierarchy', () => {
    it('should instantiate EventRuntimeException as base Error subclass', () => {
      const err = new EventRuntimeException('Runtime failure');
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(EventRuntimeException);
      expect(err.name).toBe('EventRuntimeException');
    });

    it('should instantiate EventInitializationException', () => {
      const err = new EventInitializationException('Init failed');
      expect(err).toBeInstanceOf(EventRuntimeException);
      expect(err.name).toBe('EventInitializationException');
    });

    it('should instantiate EventProviderException', () => {
      const err = new EventProviderException('Provider failed');
      expect(err).toBeInstanceOf(EventRuntimeException);
      expect(err.name).toBe('EventProviderException');
    });

    it('should instantiate EventDispatchException', () => {
      const err = new EventDispatchException('Dispatch failed');
      expect(err).toBeInstanceOf(EventRuntimeException);
      expect(err.name).toBe('EventDispatchException');
    });

    it('should instantiate EventValidationException', () => {
      const err = new EventValidationException('Validation failed');
      expect(err).toBeInstanceOf(EventRuntimeException);
      expect(err.name).toBe('EventValidationException');
    });
  });

  describe('4. EventProvider Engine & Lifecycle Transitions', () => {
    it('should start in UNINITIALIZED state', () => {
      const provider = new EventProvider();
      const state = provider.state();
      expect(state.runtimeState).toBe(EventRuntimeState.UNINITIALIZED);
      expect(state.initialized).toBe(false);

      const health = provider.health();
      expect(health.healthy).toBe(false);
    });

    it('should accept custom configuration, capabilities, and context in constructor', () => {
      const cfg = createEventConfiguration({ runtimeName: 'CustomApp' });
      const cap = createEventCapabilities({ supportsFiltering: false });
      const ctx = createEventContext({ environment: 'staging' });

      const provider = new EventProvider(cfg, cap, ctx);
      expect(provider.configuration().runtimeName).toBe('CustomApp');
      expect(provider.capabilities().supportsFiltering).toBe(false);
      expect(provider.context().environment).toBe('staging');
    });

    it('should transition to READY on initialize()', () => {
      const provider = new EventProvider();
      const health = provider.initialize();

      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(EventRuntimeState.READY);

      const state = provider.state();
      expect(state.runtimeState).toBe(EventRuntimeState.READY);
      expect(state.initialized).toBe(true);
      expect(state.startedAt).toBeDefined();
    });

    it('should handle idempotent initialize() calls without incrementing statistics', () => {
      const provider = new EventProvider();
      provider.initialize();
      const h2 = provider.initialize();

      expect(h2.healthy).toBe(true);
      expect(provider.statistics().initializations).toBe(1);
    });

    it('should transition to STOPPED on shutdown()', () => {
      const provider = new EventProvider();
      provider.initialize();

      const health = provider.shutdown();
      expect(health.healthy).toBe(false);
      expect(health.runtimeState).toBe(EventRuntimeState.STOPPED);

      const state = provider.state();
      expect(state.runtimeState).toBe(EventRuntimeState.STOPPED);
      expect(state.initialized).toBe(false);
      expect(state.startedAt).toBeNull();
    });

    it('should handle restart() transition by shutting down and re-initializing', () => {
      const provider = new EventProvider();
      provider.initialize();

      const health = provider.restart();
      expect(health.healthy).toBe(true);
      expect(health.runtimeState).toBe(EventRuntimeState.READY);

      const stats = provider.statistics();
      expect(stats.restarts).toBe(1);
      expect(stats.initializations).toBe(2);
      expect(stats.shutdowns).toBe(1);
    });

    it('should produce diagnostics snapshot containing health, stats, and capabilities', () => {
      const provider = new EventProvider();
      provider.initialize();

      const diag = provider.diagnostics();
      expect(diag.health.healthy).toBe(true);
      expect(diag.statistics.initializations).toBe(1);
      expect(diag.capabilities.supportsEventBus).toBe(true);
      expect(diag.context.environment).toBe('production');
    });
  });

  describe('5. EventRuntime Coordinator & Delegation', () => {
    it('should delegate lifecycle methods to injected provider', () => {
      const provider = new EventProvider();
      const runtime = new EventRuntime(provider);

      expect(runtime.state().runtimeState).toBe(EventRuntimeState.UNINITIALIZED);

      const h1 = runtime.initialize();
      expect(h1.healthy).toBe(true);
      expect(runtime.health().healthy).toBe(true);

      const h2 = runtime.shutdown();
      expect(h2.healthy).toBe(false);
      expect(runtime.state().runtimeState).toBe(EventRuntimeState.STOPPED);
    });

    it('should return provider reference via provider()', () => {
      const provider = new EventProvider();
      const runtime = new EventRuntime(provider);
      expect(runtime.provider()).toBe(provider);
    });

    it('should delegate statistics, capabilities, and diagnostics', () => {
      const provider = new EventProvider();
      const runtime = new EventRuntime(provider);
      runtime.initialize();

      expect(runtime.statistics().initializations).toBe(1);
      expect(runtime.capabilities().supportsPubSub).toBe(true);
      expect(runtime.diagnostics().health.healthy).toBe(true);
    });

    it('should delegate restart() method through EventRuntime', () => {
      const runtime = new EventRuntime();
      runtime.initialize();
      const health = runtime.restart();

      expect(health.healthy).toBe(true);
      expect(runtime.statistics().restarts).toBe(1);
    });
  });

  describe('6. Lazy Singleton Helpers', () => {
    it('should lazily instantiate global provider and runtime', () => {
      const p1 = getEventProvider();
      const p2 = getEventProvider();
      expect(p1).toBe(p2);

      const r1 = getEventRuntime();
      const r2 = getEventRuntime();
      expect(r1).toBe(r2);
      expect(r1.provider()).toBe(p1);
    });

    it('should allow setting custom provider and runtime', () => {
      const customP = new EventProvider();
      setEventProvider(customP);
      expect(getEventProvider()).toBe(customP);

      const customR = new EventRuntime(customP);
      setEventRuntime(customR);
      expect(getEventRuntime()).toBe(customR);
    });

    it('should reset singleton instances cleanly via resetEventRuntime()', () => {
      const r1 = getEventRuntime();
      r1.initialize();
      expect(r1.health().healthy).toBe(true);

      resetEventRuntime();

      const r2 = getEventRuntime();
      expect(r2).not.toBe(r1);
      expect(r2.health().healthy).toBe(false);
    });

    it('should reset event provider cleanly via resetEventProvider()', () => {
      const p1 = getEventProvider();
      p1.initialize();
      expect(p1.health().healthy).toBe(true);

      resetEventProvider();

      const p2 = getEventProvider();
      expect(p2).not.toBe(p1);
      expect(p2.health().healthy).toBe(false);
    });
  });
});
