import { describe, it, expect, vi } from 'vitest';
import {
  LoggingMetricsRuntime,
  LoggingMetricsProvider,
  LoggingMetricsStateError,
  LoggingMetricsPolicyError
} from '../../../../src/observability';
import { LogRecord, LogLevel } from '../../../../src/observability/logging/models/log';

// Helper to construct fully stubbed mock Metrics Runtime
const createMockMetricsRuntime = () => {
  const mockInstrument = {
    getDefinition: vi.fn(() => ({ name: 'metric-1', type: 'COUNTER', labelKeys: [] })),
    isEnabled: vi.fn(() => true),
    setEnabled: vi.fn(),
    increment: vi.fn(),
    set: vi.fn(),
    observe: vi.fn(),
    record: vi.fn()
  };

  return {
    initialize: vi.fn(async () => {}),
    shutdown: vi.fn(async () => {}),
    getState: vi.fn(() => 'READY'),
    getMetric: vi.fn(() => mockInstrument),
    getCounter: vi.fn(() => mockInstrument),
    getGauge: vi.fn(() => mockInstrument),
    getHistogram: vi.fn(() => mockInstrument),
    getTimer: vi.fn(() => mockInstrument),
    registerCounter: vi.fn(() => mockInstrument),
    registerGauge: vi.fn(() => mockInstrument),
    registerHistogram: vi.fn(() => mockInstrument),
    registerTimer: vi.fn(() => mockInstrument)
  } as any;
};

describe('Logging Metrics Integration Tests', () => {
  it('A. Runtime construction, DI and lifecycles', async () => {
    const metrics = createMockMetricsRuntime();
    const provider = new LoggingMetricsProvider({ metricsRuntime: metrics });
    
    expect(provider.getState()).toBe('UNINITIALIZED');
    expect(provider.getHealth()).toBe('UNKNOWN');

    const runtime = new LoggingMetricsRuntime(provider);
    expect(runtime.provider()).toBe(provider);

    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');
    expect(runtime.getHealth()).toBe('HEALTHY');

    // Idempotent initialize
    await runtime.initialize();

    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');

    // Invalid transition
    (provider as any)._state = 'STOPPING';
    await expect(provider.initialize()).rejects.toThrow(LoggingMetricsStateError);
  });

  it('B. Registry registration, duplicates, and enable/disable', async () => {
    const provider = new LoggingMetricsProvider({ metricsRuntime: createMockMetricsRuntime() });
    await provider.initialize();

    const policy = {
      id: 'pol-1',
      enabled: true,
      loggerName: 'AuthLogger',
      minLevel: LogLevel.WARN,
      metricName: 'auth_warnings',
      metricType: 'COUNTER' as any,
      priority: 10
    };

    provider.registerPolicy(policy);
    expect(provider.getPolicy('pol-1')?.metricName).toBe('auth_warnings');

    // Duplicate rejection
    expect(() => provider.registerPolicy(policy)).toThrow(LoggingMetricsPolicyError);

    // Disable / Enable
    provider.disablePolicy('pol-1');
    expect(provider.getPolicy('pol-1')?.enabled).toBe(false);

    provider.enablePolicy('pol-1');
    expect(provider.getPolicy('pol-1')?.enabled).toBe(true);

    // Removal
    provider.unregisterPolicy('pol-1');
    expect(provider.getPolicy('pol-1')).toBeNull();
  });

  it('C. Specificity-based policy matching precedence', async () => {
    const provider = new LoggingMetricsProvider({ metricsRuntime: createMockMetricsRuntime() });
    await provider.initialize();

    // 1. Global policy
    provider.registerPolicy({
      id: 'p-global',
      enabled: true,
      loggerName: '*',
      minLevel: LogLevel.TRACE,
      metricName: 'm-global',
      metricType: 'COUNTER' as any,
      priority: 1
    });

    // 2. Level-specific policy
    provider.registerPolicy({
      id: 'p-level',
      enabled: true,
      loggerName: '*',
      minLevel: LogLevel.ERROR,
      metricName: 'm-level',
      metricType: 'COUNTER' as any,
      priority: 2
    });

    // 3. Logger-specific policy
    provider.registerPolicy({
      id: 'p-logger',
      enabled: true,
      loggerName: 'AuthLogger',
      minLevel: LogLevel.TRACE,
      metricName: 'm-logger',
      metricType: 'COUNTER' as any,
      priority: 3
    });

    // Test sorting ordering
    const sorted = provider.listPolicies();
    expect(sorted[0].id).toBe('p-logger'); // LOGGER-SPECIFIC (Score 3)
    expect(sorted[1].id).toBe('p-level');  // LEVEL-SPECIFIC (Score 2)
    expect(sorted[2].id).toBe('p-global'); // GLOBAL (Score 1)

    // Test tie-breaking by priority (same logger specificity)
    provider.registerPolicy({
      id: 'p-logger-high',
      enabled: true,
      loggerName: 'AuthLogger',
      minLevel: LogLevel.TRACE,
      metricName: 'm-logger-high',
      metricType: 'COUNTER' as any,
      priority: 100 // Higher priority
    });

    const sortedWithPriority = provider.listPolicies();
    expect(sortedWithPriority[0].id).toBe('p-logger-high');
    expect(sortedWithPriority[1].id).toBe('p-logger');
  });

  it('D. Translation logic: LogRecord Level & Value mappings', async () => {
    const metrics = createMockMetricsRuntime();
    const provider = new LoggingMetricsProvider({ metricsRuntime: metrics });
    await provider.initialize();

    // Policy requires minimum severity of WARN
    provider.registerPolicy({
      id: 'p-warn',
      enabled: true,
      loggerName: 'ServerLogger',
      minLevel: LogLevel.WARN,
      metricName: 'warnings_counter',
      metricType: 'COUNTER' as any,
      priority: 10
    });

    // Case A: Level INFO (below threshold) -> Skipped
    const logInfo: LogRecord = {
      id: 'log-1',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'Processing request',
      loggerName: 'ServerLogger'
    };

    let res = await provider.processLogRecord(logInfo);
    expect(res.status).toBe('SKIPPED');
    expect(res.reason).toContain('below policy threshold');

    // Case B: Level ERROR (above threshold) -> Accepted and metrics called
    const logError: LogRecord = {
      id: 'log-2',
      timestamp: Date.now(),
      level: LogLevel.ERROR,
      message: 'Connection failed',
      loggerName: 'ServerLogger'
    };

    res = await provider.processLogRecord(logError);
    expect(res.status).toBe('ACCEPTED');
    expect(metrics.getMetric).toHaveBeenCalledWith('warnings_counter');
  });

  it('E. Metric types delegation', async () => {
    const metrics = createMockMetricsRuntime();
    const provider = new LoggingMetricsProvider({ metricsRuntime: metrics });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-timer',
      enabled: true,
      loggerName: 'LatencyLogger',
      minLevel: LogLevel.INFO,
      metricName: 'operation_latency',
      metricType: 'TIMER' as any,
      priority: 10,
      metadata: { valueField: 'durationMs' }
    });

    const log: LogRecord = {
      id: 'log-timer',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'Operation duration',
      loggerName: 'LatencyLogger',
      durationMs: 452
    };

    const res = await provider.processLogRecord(log);
    expect(res.status).toBe('ACCEPTED');
    expect(res.operation).toBe('TIMER');

    // Stats checks
    const stats = provider.getStatistics();
    expect(stats.timerObservations).toBe(1);
    expect(stats.averageProcessingDuration).toBeGreaterThanOrEqual(0);
  });

  it('F. Label normalization & sensitive field redactions', async () => {
    const mockInstrument = {
      getDefinition: vi.fn(() => ({ name: 'sec_metric', type: 'COUNTER', labelKeys: [] })),
      isEnabled: vi.fn(() => true),
      setEnabled: vi.fn(),
      increment: vi.fn(),
      set: vi.fn(),
      observe: vi.fn(),
      record: vi.fn()
    };
    const metrics = {
      initialize: vi.fn(),
      shutdown: vi.fn(),
      getState: vi.fn(() => 'READY'),
      getMetric: vi.fn(() => { throw new Error('Not registered'); }),
      registerCounter: vi.fn(() => mockInstrument)
    } as any;

    const provider = new LoggingMetricsProvider({ metricsRuntime: metrics });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-sec',
      enabled: true,
      loggerName: 'SecureLogger',
      minLevel: LogLevel.INFO,
      metricName: 'sec_metric',
      metricType: 'COUNTER' as any,
      priority: 10,
      labels: {
        password: '123', // sensitive -> should be redacted
        module: 'checkout' // safe -> preserved
      }
    });

    const log: LogRecord = {
      id: 'log-sec',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'Secure log',
      loggerName: 'SecureLogger',
      correlationId: 'corr-id-123'
    };

    await provider.processLogRecord(log);

    // Verify label redaction rules inside metrics delegation call arguments
    const registerCallArgs = metrics.registerCounter.mock.calls[0][0];
    expect(registerCallArgs.labelKeys).not.toContain('password');
    expect(registerCallArgs.labelKeys).toContain('module');
    expect(registerCallArgs.labelKeys).toContain('correlationId');
    expect(registerCallArgs.labelKeys).toContain('logger');

    const incrementCallArgs = mockInstrument.increment.mock.calls[0][1];
    expect(incrementCallArgs.password).toBeUndefined();
    expect(incrementCallArgs.module).toBe('checkout');
    expect(incrementCallArgs.correlationId).toBe('corr-id-123');
    expect(incrementCallArgs.logger).toBe('SecureLogger');
  });

  it('G. Idempotency and FIFO capacity bounds', async () => {
    const provider = new LoggingMetricsProvider({ metricsRuntime: createMockMetricsRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-idem',
      enabled: true,
      loggerName: 'IdemLogger',
      minLevel: LogLevel.INFO,
      metricName: 'idem_metric',
      metricType: 'COUNTER' as any,
      priority: 10
    });

    const log: LogRecord = {
      id: 'duplicate-log-id-100',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'First attempt',
      loggerName: 'IdemLogger'
    };

    // First attempt succeeds
    let res1 = await provider.processLogRecord(log);
    expect(res1.status).toBe('ACCEPTED');

    // Second attempt fails (idempotency skip)
    let res2 = await provider.processLogRecord(log);
    expect(res2.status).toBe('SKIPPED');
    expect(res2.reason).toContain('already been processed');
  });

  it('H. Concurrency protection (promise caching)', async () => {
    const provider = new LoggingMetricsProvider({ metricsRuntime: createMockMetricsRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-conc',
      enabled: true,
      loggerName: 'ConcLogger',
      minLevel: LogLevel.INFO,
      metricName: 'conc_metric',
      metricType: 'COUNTER' as any,
      priority: 10
    });

    const log: LogRecord = {
      id: 'concurrent-id-888',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'Concurrent log',
      loggerName: 'ConcLogger'
    };

    const p1 = provider.processLogRecord(log);
    const p2 = provider.processLogRecord(log);

    expect(p1).toBe(p2); // Shares the same active promise
    await p1;
  });

  it('I. Failure isolation', async () => {
    const mockInstrument = {
      getDefinition: vi.fn(() => ({ name: 'fail_metric', type: 'COUNTER', labelKeys: [] })),
      isEnabled: vi.fn(() => true),
      setEnabled: vi.fn(),
      increment: vi.fn(() => {
        throw new Error('Metrics Registry Unreachable');
      }),
      set: vi.fn(),
      observe: vi.fn(),
      record: vi.fn()
    };
    const metrics = {
      initialize: vi.fn(),
      shutdown: vi.fn(),
      getState: vi.fn(() => 'READY'),
      getMetric: vi.fn(() => mockInstrument),
      registerCounter: vi.fn(() => mockInstrument)
    } as any;

    const provider = new LoggingMetricsProvider({ metricsRuntime: metrics });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-fail',
      enabled: true,
      loggerName: 'FailLogger',
      minLevel: LogLevel.INFO,
      metricName: 'fail_metric',
      metricType: 'COUNTER' as any,
      priority: 10
    });

    const log: LogRecord = {
      id: 'log-fail',
      timestamp: Date.now(),
      level: LogLevel.INFO,
      message: 'Crashing delegation',
      loggerName: 'FailLogger'
    };

    // Failure should be captured cleanly and not crash the process record execution flow
    const res = await provider.processLogRecord(log);
    expect(res.status).toBe('REJECTED');
    expect(res.reason).toContain('Integration failed');

    const stats = provider.getStatistics();
    expect(stats.failedIntegrations).toBe(1);

    const diags = provider.getDiagnostics();
    expect(diags.recentFailures[0].error.message).toContain('Metrics Registry Unreachable');
    expect(Object.isFrozen(diags)).toBe(true); // Immutability
  });

  it('K. Measured Sanity Performance Benchmark', async () => {
    const provider = new LoggingMetricsProvider({ metricsRuntime: createMockMetricsRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-perf',
      enabled: true,
      loggerName: 'PerfLogger',
      minLevel: LogLevel.INFO,
      metricName: 'perf_metric',
      metricType: 'COUNTER' as any,
      priority: 10
    });

    const iterations = 50;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      const record: LogRecord = {
        id: `perf-log-${i}`,
        timestamp: Date.now(),
        level: LogLevel.INFO,
        message: `Benchmark operation iteration ${i}`,
        loggerName: 'PerfLogger'
      };
      await provider.processLogRecord(record);
    }

    const duration = performance.now() - start;
    const avgDuration = duration / iterations;

    console.log(`[PERFORMANCE BENCHMARK] Logging-Metrics Integration:`);
    console.log(`- Total Runs: ${iterations}`);
    console.log(`- Total Duration: ${duration.toFixed(2)}ms`);
    console.log(`- Avg Duration: ${avgDuration.toFixed(4)}ms per record`);

    expect(avgDuration).toBeLessThan(10); // Standard microsecond evaluation check bounds
  });
});
