import { describe, it, expect, vi } from 'vitest';
import {
  DiagnosticsTelemetryRuntime,
  DiagnosticsTelemetryProvider,
  DiagnosticsTelemetryStateError,
  DiagnosticsTelemetryPolicyError
} from '../../../../src/observability';
import { DiagnosticReport } from '../../../../src/observability/diagnostics/models/report';
import { DiagnosticResult } from '../../../../src/observability/diagnostics/models/result';
import { DiagnosticSeverity, DiagnosticStatus } from '../../../../src/observability/diagnostics/models/diagnostic';

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

describe('Diagnostics Telemetry Integration Tests', () => {
  it('A. Runtime construction, DI and lifecycles', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });

    expect(provider.getState()).toBe('UNINITIALIZED');
    expect(provider.getHealth()).toBe('UNKNOWN');

    const runtime = new DiagnosticsTelemetryRuntime(provider);
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
    await expect(provider.initialize()).rejects.toThrow(DiagnosticsTelemetryStateError);
  });

  it('B. Registry registration, duplicates, and enable/disable', async () => {
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    const policy = {
      id: 'pol-dt-1',
      enabled: true,
      priority: 10,
      checkId: 'cpu_usage',
      telemetryType: 'EVENT' as any,
      level: 'RESULT' as any
    };

    provider.registerPolicy(policy);
    expect(provider.getPolicy('pol-dt-1')?.checkId).toBe('cpu_usage');

    // Duplicate rejection
    expect(() => provider.registerPolicy(policy)).toThrow(DiagnosticsTelemetryPolicyError);

    // Disable / Enable
    provider.disablePolicy('pol-dt-1');
    expect(provider.getPolicy('pol-dt-1')?.enabled).toBe(false);

    provider.enablePolicy('pol-dt-1');
    expect(provider.getPolicy('pol-dt-1')?.enabled).toBe(true);

    // Removal
    provider.unregisterPolicy('pol-dt-1');
    expect(provider.getPolicy('pol-dt-1')).toBeNull();
  });

  it('C. Specificity-based policy matching precedence', async () => {
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    // 1. Global policy
    provider.registerPolicy({
      id: 'p-global',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // 2. Status-specific policy
    provider.registerPolicy({
      id: 'p-status',
      enabled: true,
      priority: 2,
      status: DiagnosticStatus.HEALTHY,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // 3. Severity-specific policy
    provider.registerPolicy({
      id: 'p-severity',
      enabled: true,
      priority: 3,
      severity: DiagnosticSeverity.ERROR,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // 4. Category-specific policy
    provider.registerPolicy({
      id: 'p-category',
      enabled: true,
      priority: 4,
      category: 'PERFORMANCE' as any,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // 5. Source-specific policy
    provider.registerPolicy({
      id: 'p-source',
      enabled: true,
      priority: 5,
      sourceId: 'db-source',
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // 6. Check-specific policy
    provider.registerPolicy({
      id: 'p-check',
      enabled: true,
      priority: 6,
      checkId: 'cpu-check',
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    // Test sorting ordering
    const sorted = provider.listPolicies();
    expect(sorted[0].id).toBe('p-check');    // Score 6
    expect(sorted[1].id).toBe('p-source');   // Score 5
    expect(sorted[2].id).toBe('p-category'); // Score 4
    expect(sorted[3].id).toBe('p-severity'); // Score 3
    expect(sorted[4].id).toBe('p-status');   // Score 2
    expect(sorted[5].id).toBe('p-global');   // Score 1

    // Test tie-breaking by priority (same specificity score)
    provider.registerPolicy({
      id: 'p-check-high',
      enabled: true,
      priority: 100, // Higher priority
      checkId: 'cpu-check',
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    const sortedWithPriority = provider.listPolicies();
    expect(sortedWithPriority[0].id).toBe('p-check-high');
    expect(sortedWithPriority[1].id).toBe('p-check');
  });

  it('D. Run-level translation: diagnostic run to telemetry record', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-run-trans',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RUN'
    });

    const report: DiagnosticReport = {
      reportId: 'rep-111',
      generatedAt: 1700000000000,
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.HEALTHY,
      overallSeverity: DiagnosticSeverity.INFO,
      sourceCount: 2,
      checkCount: 4,
      passedCount: 4,
      degradedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      results: [],
      summary: 'All checks passed',
      statistics: {
        totalEvaluations: 4,
        passedEvaluations: 4,
        failedEvaluations: 0,
        averageDuration: 5
      } as any
    };

    const res = await provider.processDiagnosticReport(report);
    expect(res[0].status).toBe('ACCEPTED');

    const emitted = telemetry.getRecords();
    expect(emitted.length).toBe(1);
    expect(emitted[0].traceId).toBeUndefined();
    expect(emitted[0].name).toBe('Diagnostics Run Report');
    expect(emitted[0].severity).toBe('INFO');
    expect(emitted[0].attributes.diagnosticStatus).toBe('HEALTHY');
    expect(emitted[0].attributes.message).toBe('All checks passed');
  });

  it('E. Result-level translation: diagnostic result to telemetry record', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-res-trans',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT',
      checkId: 'cpu_usage'
    });

    const result: DiagnosticResult = {
      checkId: 'cpu_usage',
      sourceId: 'system-agent',
      status: DiagnosticStatus.DEGRADED,
      severity: DiagnosticSeverity.WARNING,
      message: 'CPU usage is high',
      duration: 15,
      timestamp: Date.now(),
      metadata: {
        correlationId: 'c-111',
        requestId: 'r-222',
        operationId: 'o-333',
        traceId: 't-444'
      }
    };

    const report: DiagnosticReport = {
      reportId: 'rep-222',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.DEGRADED,
      overallSeverity: DiagnosticSeverity.WARNING,
      sourceCount: 1,
      checkCount: 1,
      passedCount: 0,
      degradedCount: 1,
      failedCount: 0,
      skippedCount: 0,
      results: [result],
      summary: 'Degraded',
      statistics: {} as any
    };

    const res = await provider.processDiagnosticReport(report);
    expect(res[0].status).toBe('ACCEPTED');

    const emitted = telemetry.getRecords();
    expect(emitted.length).toBe(1);
    expect(emitted[0].name).toBe('system-agent - cpu_usage');
    expect(emitted[0].severity).toBe('WARN');
    expect(emitted[0].traceId).toBe('t-444');
    expect(emitted[0].correlationId).toBe('c-111');
    expect(emitted[0].requestId).toBe('r-222');
  });

  it('F. Error normalization, circular objects, and sensitive redactions', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-err-norm',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT',
      staticAttributes: {
        password: 'password123'
      }
    });

    const circularObj: any = { a: 1 };
    circularObj.self = circularObj;

    const result: DiagnosticResult = {
      checkId: 'db_conn',
      sourceId: 'db-agent',
      status: DiagnosticStatus.UNHEALTHY,
      severity: DiagnosticSeverity.CRITICAL,
      message: 'Connection timed out',
      duration: 100,
      timestamp: Date.now(),
      metadata: {
        circle: circularObj,
        secretToken: 'secret-token-value'
      },
      error: {
        name: 'TimeoutError',
        message: 'Timeout after 10000ms',
        stack: 'TimeoutError: Timeout after 10000ms at connection.ts:24'
      }
    };

    const report: DiagnosticReport = {
      reportId: 'rep-error-test',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.UNHEALTHY,
      overallSeverity: DiagnosticSeverity.CRITICAL,
      sourceCount: 1,
      checkCount: 1,
      passedCount: 0,
      degradedCount: 0,
      failedCount: 1,
      skippedCount: 0,
      results: [result],
      summary: 'Failed',
      statistics: {} as any
    };

    await provider.processDiagnosticReport(report);
    const emitted = telemetry.getRecords();

    expect(emitted.length).toBe(1);
    expect(emitted[0].severity).toBe('FATAL');
    expect(emitted[0].attributes.error.name).toBe('TimeoutError');
    expect(emitted[0].attributes.error.message).toBe('Timeout after 10000ms');
    expect(emitted[0].attributes.password).toBe('[REDACTED]');
    expect(emitted[0].attributes.circle.self).toBe('[CIRCULAR]');
  });

  it('G. Sampling and severity-based bypass logic', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-sampling',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT',
      samplingRate: 0.0,
      bypassSamplingOnError: true
    });

    const resultHealthy: DiagnosticResult = {
      checkId: 'c1',
      sourceId: 's1',
      status: DiagnosticStatus.HEALTHY,
      severity: DiagnosticSeverity.INFO,
      message: 'Healthy check',
      duration: 5,
      timestamp: Date.now(),
      metadata: {}
    };

    const resultCritical: DiagnosticResult = {
      checkId: 'c2',
      sourceId: 's1',
      status: DiagnosticStatus.UNHEALTHY,
      severity: DiagnosticSeverity.CRITICAL,
      message: 'Critical error',
      duration: 5,
      timestamp: Date.now(),
      metadata: {}
    };

    const report: DiagnosticReport = {
      reportId: 'rep-sampling-test',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.UNHEALTHY,
      overallSeverity: DiagnosticSeverity.CRITICAL,
      sourceCount: 1,
      checkCount: 2,
      passedCount: 1,
      degradedCount: 0,
      failedCount: 1,
      skippedCount: 0,
      results: [resultHealthy, resultCritical],
      summary: 'Mixed status',
      statistics: {} as any
    };

    const res = await provider.processDiagnosticReport(report);
    expect(res[0].status).toBe('SKIPPED');  // Healthy is sampled out (INFO)
    expect(res[1].status).toBe('ACCEPTED'); // Critical bypasses sampling
  });

  it('H. Idempotency checks & FIFO bounded queue', async () => {
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-idem',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT',
      allowRepeat: false
    });

    const result: DiagnosticResult = {
      checkId: 'cpu',
      sourceId: 'sys',
      status: DiagnosticStatus.HEALTHY,
      severity: DiagnosticSeverity.INFO,
      message: 'OK',
      duration: 2,
      timestamp: Date.now(),
      metadata: {}
    };

    const report: DiagnosticReport = {
      reportId: 'rep-idem',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.HEALTHY,
      overallSeverity: DiagnosticSeverity.INFO,
      sourceCount: 1,
      checkCount: 1,
      passedCount: 1,
      degradedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      results: [result],
      summary: 'OK',
      statistics: {} as any
    };

    // First attempt -> Accepted
    const res1 = await provider.processDiagnosticReport(report);
    expect(res1[0].status).toBe('ACCEPTED');

    // Duplicate attempt -> Skipped
    const res2 = await provider.processDiagnosticReport(report);
    expect(res2[0].status).toBe('SKIPPED');
  });

  it('I. Concurrency protection (promise sharing)', async () => {
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-conc',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    const report: DiagnosticReport = {
      reportId: 'rep-concurrent-999',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.HEALTHY,
      overallSeverity: DiagnosticSeverity.INFO,
      sourceCount: 0,
      checkCount: 0,
      passedCount: 0,
      degradedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      results: [],
      summary: 'OK',
      statistics: {} as any
    };

    const p1 = provider.processDiagnosticReport(report);
    const p2 = provider.processDiagnosticReport(report);

    expect(p1).toBe(p2);
    await p1;
  });

  it('K. Failure isolation', async () => {
    const telemetry = createMockTelemetryRuntime();
    telemetry.record.mockImplementationOnce(() => {
      throw new Error('Telemetry exporters unreachable');
    });

    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-fail-iso',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RUN'
    });

    const report: DiagnosticReport = {
      reportId: 'rep-fail-iso',
      generatedAt: Date.now(),
      runtimeState: 'READY',
      overallStatus: DiagnosticStatus.HEALTHY,
      overallSeverity: DiagnosticSeverity.INFO,
      sourceCount: 0,
      checkCount: 0,
      passedCount: 0,
      degradedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      results: [],
      summary: 'OK',
      statistics: {} as any
    };

    const res = await provider.processDiagnosticReport(report);
    expect(res[0].status).toBe('REJECTED');
    expect(res[0].reason).toContain('Run integration failed');

    const diags = provider.getDiagnostics();
    expect(diags.statistics.failedIntegrations).toBe(1);
    expect(diags.recentFailures[0].error.message).toContain('Telemetry exporters unreachable');
    expect(Object.isFrozen(diags)).toBe(true);
  });

  it('L. Measured Sanity Performance Benchmark', async () => {
    const provider = new DiagnosticsTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p-perf',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT' as any,
      level: 'RESULT'
    });

    const iterations = 50;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      const result: DiagnosticResult = {
        checkId: `c-${i}`,
        sourceId: 'sys-agent',
        status: DiagnosticStatus.HEALTHY,
        severity: DiagnosticSeverity.INFO,
        message: 'Benchmark check',
        duration: 1,
        timestamp: Date.now(),
        metadata: {}
      };
      const report: DiagnosticReport = {
        reportId: `rep-perf-${i}`,
        generatedAt: Date.now(),
        runtimeState: 'READY',
        overallStatus: DiagnosticStatus.HEALTHY,
        overallSeverity: DiagnosticSeverity.INFO,
        sourceCount: 1,
        checkCount: 1,
        passedCount: 1,
        degradedCount: 0,
        failedCount: 0,
        skippedCount: 0,
        results: [result],
        summary: 'Perf iteration',
        statistics: {} as any
      };
      await provider.processDiagnosticReport(report);
    }

    const duration = performance.now() - start;
    const avgDuration = duration / iterations;

    console.log(`[PERFORMANCE BENCHMARK] Diagnostics-Telemetry Integration:`);
    console.log(`- Total Runs: ${iterations}`);
    console.log(`- Total Duration: ${duration.toFixed(2)}ms`);
    console.log(`- Avg Duration: ${avgDuration.toFixed(4)}ms per report`);

    expect(avgDuration).toBeLessThan(10);
  });
});
