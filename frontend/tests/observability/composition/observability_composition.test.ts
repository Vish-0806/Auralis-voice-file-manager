import { describe, it, expect, vi } from 'vitest';
import {
  ObservabilityCompositionProvider,
  ObservabilityRuntime,
  ObservabilityCompositionState,
  ObservabilityCompositionStateError,
  ObservabilityCompositionInitializationError,
  ObservabilityCompositionShutdownError
} from '../../../src/observability';

// Helper to construct fully stubbed mock subsystems
const createMockSubsystem = (_name: string, initialState = 'UNINITIALIZED') => {
  let state = initialState;
  const health = { status: 'HEALTHY' as const };
  return {
    initialize: vi.fn(async () => {
      state = 'READY';
    }),
    shutdown: vi.fn(async () => {
      state = 'STOPPED';
    }),
    getState: vi.fn(() => state),
    getHealth: vi.fn(() => health),
    getStatistics: vi.fn(() => ({})),
    getDiagnostics: vi.fn(() => ({})),
    setState: (s: string) => { state = s; },
    setHealthStatus: (s: any) => { health.status = s; }
  } as any;
};

describe('Observability Runtime Composition Tests', () => {
  it('1. Default provider construction', () => {
    const provider = new ObservabilityCompositionProvider();
    expect(provider.monitoring()).toBeDefined();
    expect(provider.logging()).toBeDefined();
    expect(provider.metrics()).toBeDefined();
    expect(provider.tracing()).toBeDefined();
    expect(provider.telemetry()).toBeDefined();
    expect(provider.diagnostics()).toBeDefined();
    expect(provider.alerting()).toBeDefined();
  });

  it('2. Dependency injection & initial state', () => {
    const monitoring = createMockSubsystem('monitoring');
    const provider = new ObservabilityCompositionProvider({ monitoring });
    expect(provider.monitoring()).toBe(monitoring);
    expect(provider.getState()).toBe(ObservabilityCompositionState.UNINITIALIZED);
  });

  it('3. Successful initialization & exact order', async () => {
    const callOrder: string[] = [];
    const createOrderedMock = (name: string) => {
      const mock = createMockSubsystem(name);
      mock.initialize.mockImplementation(async () => {
        callOrder.push(name);
        mock.setState('READY');
      });
      return mock;
    };

    const monitoring = createOrderedMock('monitoring');
    const logging = createOrderedMock('logging');
    const metrics = createOrderedMock('metrics');
    const tracing = createOrderedMock('tracing');
    const telemetry = createOrderedMock('telemetry');
    const diagnostics = createOrderedMock('diagnostics');
    const alerting = createOrderedMock('alerting');

    const runtime = new ObservabilityRuntime(
      new ObservabilityCompositionProvider({
        monitoring,
        logging,
        metrics,
        tracing,
        telemetry,
        diagnostics,
        alerting
      })
    );

    await runtime.initialize();

    expect(runtime.getState()).toBe(ObservabilityCompositionState.READY);
    expect(callOrder).toEqual([
      'monitoring',
      'logging',
      'metrics',
      'tracing',
      'telemetry',
      'diagnostics',
      'alerting'
    ]);
  });

  it('4. Successful shutdown & reverse order', async () => {
    const callOrder: string[] = [];
    const createOrderedMock = (name: string) => {
      const mock = createMockSubsystem(name, 'READY');
      mock.shutdown.mockImplementation(async () => {
        callOrder.push(name);
        mock.setState('STOPPED');
      });
      return mock;
    };

    const monitoring = createOrderedMock('monitoring');
    const logging = createOrderedMock('logging');
    const metrics = createOrderedMock('metrics');
    const tracing = createOrderedMock('tracing');
    const telemetry = createOrderedMock('telemetry');
    const diagnostics = createOrderedMock('diagnostics');
    const alerting = createOrderedMock('alerting');

    const provider = new ObservabilityCompositionProvider({
      monitoring,
      logging,
      metrics,
      tracing,
      telemetry,
      diagnostics,
      alerting
    });
    // Set internal state to READY to allow shutdown
    (provider as any)._state = ObservabilityCompositionState.READY;

    const runtime = new ObservabilityRuntime(provider);
    await runtime.shutdown();

    expect(runtime.getState()).toBe(ObservabilityCompositionState.STOPPED);
    expect(callOrder).toEqual([
      'alerting',
      'diagnostics',
      'telemetry',
      'tracing',
      'metrics',
      'logging',
      'monitoring'
    ]);
  });

  it('5. Initialization & shutdown idempotency', async () => {
    const monitoring = createMockSubsystem('monitoring');
    const provider = new ObservabilityCompositionProvider({ monitoring });
    const runtime = new ObservabilityRuntime(provider);

    await runtime.initialize();
    await runtime.initialize(); // Second call should do nothing

    expect(monitoring.initialize).toHaveBeenCalledTimes(1);

    await runtime.shutdown();
    await runtime.shutdown(); // Second call should do nothing

    expect(monitoring.shutdown).toHaveBeenCalledTimes(1);
  });

  it('6. Concurrent initialization & shutdown promise sharing', async () => {
    const monitoring = createMockSubsystem('monitoring');
    const provider = new ObservabilityCompositionProvider({ monitoring });
    const runtime = new ObservabilityRuntime(provider);

    const p1 = runtime.initialize();
    const p2 = runtime.initialize();

    expect(p1).toBe(p2);
    await p1;

    const p3 = runtime.shutdown();
    const p4 = runtime.shutdown();

    expect(p3).toBe(p4);
    await p3;
  });

  it('7. Initialization failure & compensation logic', async () => {
    const monitoring = createMockSubsystem('monitoring');
    const logging = createMockSubsystem('logging');
    const metrics = createMockSubsystem('metrics');
    metrics.initialize.mockImplementation(async () => {
      throw new Error('Metrics Error');
    });

    const provider = new ObservabilityCompositionProvider({
      monitoring,
      logging,
      metrics
    });
    const runtime = new ObservabilityRuntime(provider);

    await expect(runtime.initialize()).rejects.toThrow(
      ObservabilityCompositionInitializationError
    );

    expect(runtime.getState()).toBe(ObservabilityCompositionState.FAILED);
    expect(monitoring.shutdown).toHaveBeenCalledTimes(1);
    expect(logging.shutdown).toHaveBeenCalledTimes(1);
    expect(metrics.shutdown).not.toHaveBeenCalled(); // Failed to initialize, should not shutdown
  });

  it('8. Shutdown failure isolation', async () => {
    const monitoring = createMockSubsystem('monitoring', 'READY');
    const logging = createMockSubsystem('logging', 'READY');
    logging.shutdown.mockImplementation(async () => {
      throw new Error('Logging shutdown failed');
    });

    const provider = new ObservabilityCompositionProvider({
      monitoring,
      logging
    });
    (provider as any)._state = ObservabilityCompositionState.READY;

    const runtime = new ObservabilityRuntime(provider);

    await expect(runtime.shutdown()).rejects.toThrow(
      ObservabilityCompositionShutdownError
    );

    expect(runtime.getState()).toBe(ObservabilityCompositionState.FAILED);
    expect(monitoring.shutdown).toHaveBeenCalledTimes(1); // Still runs despite logging crash
  });

  it('9. Health aggregation rules', async () => {
    const monitoring = createMockSubsystem('monitoring', 'UNINITIALIZED');
    monitoring.setHealthStatus('UNKNOWN');
    const logging = createMockSubsystem('logging', 'UNINITIALIZED');

    const provider = new ObservabilityCompositionProvider({
      monitoring,
      logging
    });
    const runtime = new ObservabilityRuntime(provider);

    // Initial state check
    let health = runtime.getHealth();
    expect(health.status).toBe('UNKNOWN');

    // Make monitoring unhealthy
    monitoring.setHealthStatus('UNHEALTHY');
    health = runtime.getHealth();
    expect(health.status).toBe('UNHEALTHY');
    expect(health.unhealthySubsystemCount).toBe(1);

    // Make monitoring degraded, logging healthy
    monitoring.setHealthStatus('DEGRADED');
    logging.setState('READY');
    health = runtime.getHealth();
    expect(health.status).toBe('DEGRADED');
    expect(health.degradedSubsystemCount).toBe(1);
    expect(health.healthySubsystemCount).toBe(1);
  });

  it('10. Diagnostics immutability & statistics checks', async () => {
    const provider = new ObservabilityCompositionProvider();
    const runtime = new ObservabilityRuntime(provider);

    await runtime.initialize();

    const diags = runtime.getDiagnostics();
    expect(diags.compositionState).toBe(ObservabilityCompositionState.READY);
    expect(Object.isFrozen(diags)).toBe(true);

    const stats = runtime.getStatistics();
    expect(stats.initializationCount).toBe(1);
    expect(stats.shutdownCount).toBe(0);
    expect(Object.isFrozen(stats)).toBe(true);
  });

  it('11. Invalid lifecycle transitions', async () => {
    const provider = new ObservabilityCompositionProvider();
    const runtime = new ObservabilityRuntime(provider);

    (provider as any)._state = ObservabilityCompositionState.STOPPING;

    await expect(runtime.initialize()).rejects.toThrow(
      ObservabilityCompositionStateError
    );
  });
});
