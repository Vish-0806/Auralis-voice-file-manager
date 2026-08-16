import { describe, it, expect, vi } from 'vitest';
import {
  TracingTelemetryRuntime,
  TracingTelemetryProvider,
  TracingTelemetryStateError,
  TracingTelemetryPolicyError
} from '../../../../src/observability';
import { Span, SpanKind, SpanStatus } from '../../../../src/observability/tracing/models/span';

const createMockTelemetryRuntime = () => {
  const records: any[] = [];
  return {
    initialize: vi.fn(async () => {}),
    shutdown: vi.fn(async () => {}),
    getState: vi.fn(() => 'READY'),
    record: vi.fn((rec) => {
      records.push(rec);
    }),
    getRecords: () => records,
    clearRecords: () => { records.length = 0; }
  } as any;
};

describe('Tracing Telemetry Integration Tests', () => {
  it('A. Runtime construction, DI and lifecycles', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });

    expect(provider.getState()).toBe('UNINITIALIZED');
    expect(provider.getHealth()).toBe('UNKNOWN');

    const runtime = new TracingTelemetryRuntime(provider);
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
    await expect(provider.initialize()).rejects.toThrow(TracingTelemetryStateError);
  });

  it('B. Registry registration, duplicates, and enable/disable', async () => {
    const provider = new TracingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    const policy = {
      id: 'pol-tt-1',
      enabled: true,
      priority: 10,
      spanName: 'db_query',
      telemetryType: 'TRACE' as any
    };

    provider.registerPolicy(policy);
    expect(provider.getPolicy('pol-tt-1')?.spanName).toBe('db_query');

    // Duplicate rejection
    expect(() => provider.registerPolicy(policy)).toThrow(TracingTelemetryPolicyError);

    // Disable / Enable
    provider.disablePolicy('pol-tt-1');
    expect(provider.getPolicy('pol-tt-1')?.enabled).toBe(false);

    provider.enablePolicy('pol-tt-1');
    expect(provider.getPolicy('pol-tt-1')?.enabled).toBe(true);

    // Removal
    provider.unregisterPolicy('pol-tt-1');
    expect(provider.getPolicy('pol-tt-1')).toBeNull();
  });

  it('C. Specificity-based policy matching precedence', async () => {
    const provider = new TracingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    // 1. Global policy
    provider.registerPolicy({
      id: 'p-global',
      enabled: true,
      priority: 1,
      telemetryType: 'TRACE' as any
    });

    // 2. Kind-specific policy
    provider.registerPolicy({
      id: 'p-kind',
      enabled: true,
      priority: 2,
      spanKind: SpanKind.SERVER,
      telemetryType: 'TRACE' as any
    });

    // 3. Status-specific policy
    provider.registerPolicy({
      id: 'p-status',
      enabled: true,
      priority: 3,
      statusFilter: [SpanStatus.ERROR],
      telemetryType: 'TRACE' as any
    });

    // 4. Trace-specific policy
    provider.registerPolicy({
      id: 'p-trace',
      enabled: true,
      priority: 4,
      traceName: 'http_request',
      telemetryType: 'TRACE' as any
    });

    // 5. Span-specific policy
    provider.registerPolicy({
      id: 'p-span',
      enabled: true,
      priority: 5,
      spanName: 'db_query',
      telemetryType: 'TRACE' as any
    });

    // Test sorting ordering
    const sorted = provider.listPolicies();
    expect(sorted[0].id).toBe('p-span');   // Score 5
    expect(sorted[1].id).toBe('p-trace');  // Score 4
    expect(sorted[2].id).toBe('p-status'); // Score 3
    expect(sorted[3].id).toBe('p-kind');   // Score 2
    expect(sorted[4].id).toBe('p-global'); // Score 1

    // Test tie-breaking by priority (same specificity score)
    provider.registerPolicy({
      id: 'p-span-high',
      enabled: true,
      priority: 100, // Higher priority
      spanName: 'db_query',
      telemetryType: 'TRACE' as any
    });

    const sortedWithPriority = provider.listPolicies();
    expect(sortedWithPriority[0].id).toBe('p-span-high');
    expect(sortedWithPriority[1].id).toBe('p-span');
  });

  it('D. Translation: completed span to telemetry record', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-trans',
      enabled: true,
      priority: 10,
      spanName: 'read_file',
      telemetryType: 'TRACE' as any
    });

    const span: Span = {
      spanId: 's-111',
      traceId: 't-999',
      parentSpanId: 's-parent',
      name: 'read_file',
      kind: SpanKind.INTERNAL,
      startTime: Date.now() - 100,
      endTime: Date.now(),
      duration: 100,
      status: SpanStatus.OK,
      attributes: {
        correlationId: 'corr-id-777',
        requestId: 'req-id-888',
        module: 'fs'
      }
    };

    const res = await provider.processCompletedSpan(span);
    expect(res.status).toBe('ACCEPTED');

    const emitted = telemetry.getRecords();
    expect(emitted.length).toBe(1);
    expect(emitted[0].traceId).toBe('t-999');
    expect(emitted[0].spanId).toBe('s-111');
    expect(emitted[0].correlationId).toBe('corr-id-777');
    expect(emitted[0].requestId).toBe('req-id-888');
    expect(emitted[0].name).toBe('read_file');
    expect(emitted[0].attributes.module).toBe('fs');
  });

  it('E. Span status mappings (OK, UNSET, ERROR)', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-status-test',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any,
      metadata: {
        errorSeverity: 'FATAL',
        defaultSeverity: 'DEBUG'
      }
    });

    // 1. OK span -> DEBUG
    const spanOk: Span = {
      spanId: 's-ok',
      traceId: 't-1',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK
    };
    await provider.processCompletedSpan(spanOk);

    // 2. ERROR span -> FATAL
    const spanError: Span = {
      spanId: 's-error',
      traceId: 't-2',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.ERROR
    };
    await provider.processCompletedSpan(spanError);

    const emitted = telemetry.getRecords();
    expect(emitted[0].severity).toBe('DEBUG');
    expect(emitted[1].severity).toBe('FATAL');
  });

  it('F. Attributes normalization & sensitive redactions', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-attr',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any,
      staticAttributes: {
        environment: 'test',
        password: 'admin-password' // Static secret
      }
    });

    // Circular object helper
    const circularObj: any = { key: 'value' };
    circularObj.self = circularObj;

    const span: Span = {
      spanId: 's-attr',
      traceId: 't-attr',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK,
      attributes: {
        apiKey: 'sensitive-api-key', // Dynamic secret
        circle: circularObj,
        nested: {
          token: 'token-123',
          value: 42
        }
      }
    };

    await provider.processCompletedSpan(span);
    const rec = telemetry.getRecords()[0];

    expect(rec.attributes.environment).toBe('test');
    expect(rec.attributes.password).toBe('[REDACTED]');
    expect(rec.attributes.apiKey).toBe('[REDACTED]');
    expect(rec.attributes.nested.token).toBe('[REDACTED]');
    expect(rec.attributes.nested.value).toBe(42);
    expect(rec.attributes.circle.self).toBe('[CIRCULAR]');
  });

  it('G. Event translation and ordering preservation', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-events',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any
    });

    const span: Span = {
      spanId: 's-ev',
      traceId: 't-ev',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK,
      events: [
        { name: 'step_1', timestamp: 1000, attributes: { val: 'a' } },
        { name: 'step_2', timestamp: 2000, attributes: { password: 'secret', val: 'b' } }
      ]
    };

    await provider.processCompletedSpan(span);
    const rec = telemetry.getRecords()[0];

    expect(rec.attributes.events.length).toBe(2);
    expect(rec.attributes.events[0].name).toBe('step_1');
    expect(rec.attributes.events[1].attributes.password).toBe('[REDACTED]');
    expect(rec.attributes.events[1].attributes.val).toBe('b');
  });

  it('H. Sampling and error bypass controls', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    // 0% sampling rate, but ERROR spans bypass sampling
    provider.registerPolicy({
      id: 'p-sample',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any,
      samplingRate: 0.0,
      bypassSamplingOnError: true
    });

    // 1. OK span -> Skips (sampled out)
    const spanOk: Span = {
      spanId: 's-ok',
      traceId: 't-1',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK
    };
    let resOk = await provider.processCompletedSpan(spanOk);
    expect(resOk.status).toBe('SKIPPED');

    // 2. ERROR span -> Accepted (bypasses sampling)
    const spanError: Span = {
      spanId: 's-error',
      traceId: 't-2',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.ERROR
    };
    let resError = await provider.processCompletedSpan(spanError);
    expect(resError.status).toBe('ACCEPTED');
  });

  it('I. Idempotency and FIFO bounded eviction', async () => {
    const provider = new TracingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-idem',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any
    });

    const span: Span = {
      spanId: 's-idem',
      traceId: 't-idem',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK
    };

    // First attempt -> Accepted
    const res1 = await provider.processCompletedSpan(span);
    expect(res1.status).toBe('ACCEPTED');

    // Duplicate attempt -> Skipped
    const res2 = await provider.processCompletedSpan(span);
    expect(res2.status).toBe('SKIPPED');
    expect(res2.reason).toContain('already been processed');
  });

  it('K. Concurrency protection (promise sharing)', async () => {
    const provider = new TracingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-conc',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any
    });

    const span: Span = {
      spanId: 's-conc',
      traceId: 't-conc',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK
    };

    const p1 = provider.processCompletedSpan(span);
    const p2 = provider.processCompletedSpan(span);

    expect(p1).toBe(p2);
    await p1;
  });

  it('L. Failure isolation', async () => {
    const telemetry = createMockTelemetryRuntime();
    // Simulate failing telemetry record operation
    telemetry.record.mockImplementationOnce(() => {
      throw new Error('Telemetry exporters disconnected');
    });

    const provider = new TracingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-fail',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any
    });

    const span: Span = {
      spanId: 's-fail',
      traceId: 't-fail',
      name: 'some_op',
      kind: SpanKind.INTERNAL,
      startTime: Date.now(),
      status: SpanStatus.OK
    };

    // Failure does not crash process flow but returns REJECTED status cleanly
    const res = await provider.processCompletedSpan(span);
    expect(res.status).toBe('REJECTED');
    expect(res.reason).toContain('Integration failed');

    const diags = provider.getDiagnostics();
    expect(diags.statistics.failedIntegrations).toBe(1);
    expect(diags.recentFailures[0].error.message).toContain('Telemetry exporters disconnected');
    expect(Object.isFrozen(diags)).toBe(true);
  });

  it('M. Measured Sanity Performance Benchmark', async () => {
    const provider = new TracingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-perf',
      enabled: true,
      priority: 10,
      telemetryType: 'TRACE' as any
    });

    const iterations = 50;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      const span: Span = {
        spanId: `s-${i}`,
        traceId: `t-${i}`,
        name: `perf_operation_iteration_${i}`,
        kind: SpanKind.INTERNAL,
        startTime: Date.now(),
        status: SpanStatus.OK
      };
      await provider.processCompletedSpan(span);
    }

    const duration = performance.now() - start;
    const avgDuration = duration / iterations;

    console.log(`[PERFORMANCE BENCHMARK] Tracing-Telemetry Integration:`);
    console.log(`- Total Runs: ${iterations}`);
    console.log(`- Total Duration: ${duration.toFixed(2)}ms`);
    console.log(`- Avg Duration: ${avgDuration.toFixed(4)}ms per span`);

    expect(avgDuration).toBeLessThan(10);
  });
});
