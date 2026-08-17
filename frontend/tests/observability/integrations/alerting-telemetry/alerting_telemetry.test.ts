import { describe, it, expect, vi } from 'vitest';
import {
  AlertingTelemetryRuntime,
  AlertingTelemetryProvider,
  AlertingTelemetryStateError,
  AlertingTelemetryPolicyError
} from '../../../../src/observability';
import { AlertingTelemetryTrigger, AlertingTelemetryPolicy } from '../../../../src/observability/integrations/alerting-telemetry/models';

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

describe('Alerting Telemetry Integration Tests', () => {
  it('1. Provider construction, DI and lifecycles', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });

    expect(provider.getState()).toBe('UNINITIALIZED');
    expect(provider.getHealth()).toBe('UNKNOWN');

    const runtime = new AlertingTelemetryRuntime(provider);
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
    await expect(provider.initialize()).rejects.toThrow(AlertingTelemetryStateError);
  });

  it('2. Policy registration, duplicates, and enable/disable', async () => {
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    const policy: AlertingTelemetryPolicy = {
      id: 'pol-at-1',
      enabled: true,
      priority: 10,
      alertId: 'alert-123',
      telemetryType: 'EVENT'
    };

    provider.registerPolicy(policy);
    expect(provider.getPolicy('pol-at-1')?.alertId).toBe('alert-123');

    // Duplicate rejection
    expect(() => provider.registerPolicy(policy)).toThrow(AlertingTelemetryPolicyError);

    // Disable / Enable
    provider.disablePolicy('pol-at-1');
    expect(provider.getPolicy('pol-at-1')?.enabled).toBe(false);

    provider.enablePolicy('pol-at-1');
    expect(provider.getPolicy('pol-at-1')?.enabled).toBe(true);

    // Removal
    provider.unregisterPolicy('pol-at-1');
    expect(provider.getPolicy('pol-at-1')).toBeNull();
  });

  it('3. Specificity precedence and tie-breaking', async () => {
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    // Register policies with different specificity scores
    provider.registerPolicy({
      id: 'p-global',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-status',
      enabled: true,
      priority: 2,
      status: 'ACTIVE',
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-severity',
      enabled: true,
      priority: 3,
      severity: 'CRITICAL',
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-source',
      enabled: true,
      priority: 4,
      sourceId: 'src-1',
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-rule',
      enabled: true,
      priority: 5,
      ruleId: 'rule-1',
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-fingerprint',
      enabled: true,
      priority: 6,
      fingerprint: 'fp-1',
      telemetryType: 'EVENT'
    });

    provider.registerPolicy({
      id: 'p-alert',
      enabled: true,
      priority: 7,
      alertId: 'alert-1',
      telemetryType: 'EVENT'
    });

    const sorted = provider.listPolicies();
    expect(sorted[0].id).toBe('p-alert');       // Score 7
    expect(sorted[1].id).toBe('p-fingerprint'); // Score 6
    expect(sorted[2].id).toBe('p-rule');        // Score 5
    expect(sorted[3].id).toBe('p-source');      // Score 4
    expect(sorted[4].id).toBe('p-severity');    // Score 3
    expect(sorted[5].id).toBe('p-status');      // Score 2
    expect(sorted[6].id).toBe('p-global');      // Score 1

    // Tie-breaking: priority and alphabetical ID
    const p1 = new AlertingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await p1.initialize();

    p1.registerPolicy({
      id: 'p-tie-b',
      enabled: true,
      priority: 10,
      ruleId: 'rule-x',
      telemetryType: 'EVENT'
    });
    p1.registerPolicy({
      id: 'p-tie-a',
      enabled: true,
      priority: 10,
      ruleId: 'rule-x',
      telemetryType: 'EVENT'
    });
    p1.registerPolicy({
      id: 'p-tie-c',
      enabled: true,
      priority: 5,
      ruleId: 'rule-x',
      telemetryType: 'EVENT'
    });

    const list = p1.listPolicies();
    expect(list[0].id).toBe('p-tie-a'); // priority 10, alphabetical wins over p-tie-b
    expect(list[1].id).toBe('p-tie-b'); // priority 10
    expect(list[2].id).toBe('p-tie-c'); // priority 5
  });

  it('4. Policy validation errors', async () => {
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    expect(() => provider.registerPolicy({ id: '', enabled: true, priority: 1, telemetryType: 'EVENT' })).toThrow(AlertingTelemetryPolicyError);
    expect(() => provider.registerPolicy({ id: 'valid', enabled: true, priority: undefined as any, telemetryType: 'EVENT' })).toThrow(AlertingTelemetryPolicyError);
    expect(() => provider.registerPolicy({ id: 'valid2', enabled: true, priority: 1, telemetryType: '' as any })).toThrow(AlertingTelemetryPolicyError);
  });

  it('5. Event conversion mapping for various kinds', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-general',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-1',
      kind: 'LIFECYCLE_CHANGED',
      timestamp: Date.now(),
      alertId: 'alert-lifecycle',
      fingerprint: 'fp-lifecycle',
      ruleId: 'rule-lifecycle',
      sourceId: 'src-lifecycle',
      lifecycleState: 'ACKNOWLEDGED',
      severity: 'WARNING',
      status: 'lifecycle-ok',
      correlationId: 'corr-id-123',
      traceId: 'trace-id-456'
    };

    const result = await provider.integrate(trigger);
    expect(result.status).toBe('ACCEPTED');

    const records = telemetry.getRecords();
    expect(records.length).toBe(1);
    const rec = records[0];

    expect(rec.type).toBe('EVENT');
    expect(rec.name).toBe('Alerting Event: LIFECYCLE_CHANGED - alert-lifecycle');
    expect(rec.severity).toBe('WARN'); // WARNING mapped to WARN
    expect(rec.correlationId).toBe('corr-id-123');
    expect(rec.traceId).toBe('trace-id-456');
    expect(rec.attributes.kind).toBe('LIFECYCLE_CHANGED');
    expect(rec.attributes.lifecycleState).toBe('ACKNOWLEDGED');
    expect(rec.attributes.alertSeverity).toBe('WARNING');
    expect(rec.attributes.status).toBe('lifecycle-ok');
    expect(rec.attributes.fingerprint).toBe('fp-lifecycle');
  });

  it('6. Correlation propagation and Sensitive Data Redaction', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-redact',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-redact',
      kind: 'GENERATED',
      timestamp: Date.now(),
      alertId: 'alert-redact',
      correlationId: 'corr-999',
      metadata: {
        normalField: 'hello',
        password: 'super-secret-password',
        authSecret: 'api-token'
      },
      payload: {
        token: 'secret-auth-token',
        user: {
          client_secret: 'some-oauth-client-secret',
          username: 'admin'
        }
      }
    };

    await provider.integrate(trigger);
    const records = telemetry.getRecords();
    const rec = records[0];

    expect(rec.correlationId).toBe('corr-999');
    expect(rec.attributes.normalField).toBe('hello');
    expect(rec.attributes.password).toBe('[REDACTED]');
    expect(rec.attributes.authSecret).toBe('[REDACTED]');
    expect(rec.attributes.payload.token).toBe('[REDACTED]');
    expect(rec.attributes.payload.user.client_secret).toBe('[REDACTED]');
    expect(rec.attributes.payload.user.username).toBe('admin');
  });

  it('7. Circular Reference Handling in redaction', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-circular',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const payload: any = {
      name: 'circular'
    };
    payload.self = payload; // circular

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-circular',
      kind: 'EVALUATED',
      timestamp: Date.now(),
      payload
    };

    await provider.integrate(trigger);
    const records = telemetry.getRecords();
    expect(records[0].attributes.payload.self).toBe('[CIRCULAR]');
  });

  it('8. Historical Idempotency and allowRepeat behavior', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-idemp',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT',
      allowRepeat: false
    });

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-idemp',
      kind: 'SUPPRESSED',
      timestamp: 1600000000,
      alertId: 'alert-idemp',
      fingerprint: 'fp-idemp',
      lifecycleState: 'CLOSED'
    };

    const res1 = await provider.integrate(trigger);
    const res2 = await provider.integrate(trigger);

    expect(res1.status).toBe('ACCEPTED');
    expect(res2.status).toBe('SKIPPED');
    expect(res2.reason).toContain('Duplicate event found');

    const stats = provider.statistics();
    expect(stats.duplicateEvents).toBe(1);
    expect(stats.skippedIntegrations).toBe(1);

    // Allow repeat
    const p2 = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await p2.initialize();
    p2.registerPolicy({
      id: 'pol-repeat',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT',
      allowRepeat: true
    });

    const res3 = await p2.integrate(trigger);
    const res4 = await p2.integrate(trigger);
    expect(res3.status).toBe('ACCEPTED');
    expect(res4.status).toBe('ACCEPTED');
  });

  it('9. Concurrent Promise deduplication', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-concurrent',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-concurrent',
      kind: 'ORCHESTRATION_COMPLETED',
      timestamp: 1700000000,
      alertId: 'alert-concurrent'
    };

    const p1 = provider.integrate(trigger);
    const p2 = provider.integrate(trigger);

    expect(p1).toBe(p2);
    const r1 = await p1;
    const r2 = await p2;
    expect(r1.status).toBe('ACCEPTED');
    expect(r2.status).toBe('ACCEPTED');

    expect(telemetry.getRecords().length).toBe(1); // recorded once
  });

  it('10. Telemetry dispatch failure isolation', async () => {
    const telemetry = createMockTelemetryRuntime();
    telemetry.record.mockImplementationOnce(() => {
      throw new Error('Telemetry buffer overflow');
    });

    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-overflow',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const trigger: AlertingTelemetryTrigger = {
      triggerId: 'trg-overflow',
      kind: 'NOTIFICATION_DISPATCHED',
      timestamp: Date.now()
    };

    const result = await provider.integrate(trigger);
    expect(result.status).toBe('REJECTED');
    expect(result.reason).toContain('Integration failed');

    const stats = provider.statistics();
    expect(stats.failedIntegrations).toBe(1);
    expect(stats.telemetryDispatchFailures).toBe(1);

    const diags = provider.diagnostics();
    expect(diags.recentFailures.length).toBe(1);
    expect(diags.recentFailures[0].error.message).toContain('Telemetry buffer overflow');
    expect(Object.isFrozen(diags)).toBe(true);
  });

  it('11. Batch processing independently and order preservation', async () => {
    const telemetry = createMockTelemetryRuntime();
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: telemetry });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-batch',
      enabled: true,
      priority: 1,
      telemetryType: 'EVENT'
    });

    const triggers: AlertingTelemetryTrigger[] = [
      { triggerId: 'b-1', kind: 'EVALUATED', timestamp: Date.now(), alertId: 'a-1' },
      { triggerId: 'b-2', kind: 'GENERATED', timestamp: Date.now(), alertId: 'a-2' },
      { triggerId: 'b-3', kind: 'DEDUPLICATED', timestamp: Date.now(), alertId: 'a-3' }
    ];

    const results = await provider.integrateBatch(triggers);
    expect(results.length).toBe(3);
    expect(results[0].status).toBe('ACCEPTED');
    expect(results[1].status).toBe('ACCEPTED');
    expect(results[2].status).toBe('ACCEPTED');

    const stats = provider.statistics();
    expect(stats.batchCount).toBe(1);
    expect(stats.batchItemCount).toBe(3);
  });

  it('12. Measured Sanity Performance Benchmark', async () => {
    const provider = new AlertingTelemetryProvider({ telemetryRuntime: createMockTelemetryRuntime() });
    await provider.initialize();

    provider.registerPolicy({
      id: 'pol-perf',
      enabled: true,
      priority: 10,
      telemetryType: 'EVENT'
    });

    const iterations = 50;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      const trigger: AlertingTelemetryTrigger = {
        triggerId: `perf-trg-${i}`,
        kind: 'EVALUATED',
        timestamp: Date.now() + i,
        alertId: `alert-perf-${i}`,
        ruleId: 'rule-perf',
        severity: 'INFO',
        status: 'evaluated-ok'
      };
      await provider.integrate(trigger);
    }

    const duration = performance.now() - start;
    const avgDuration = duration / iterations;

    console.log(`[PERFORMANCE BENCHMARK] Alerting-Telemetry Integration:`);
    console.log(`- Total Runs: ${iterations}`);
    console.log(`- Total Duration: ${duration.toFixed(2)}ms`);
    console.log(`- Avg Duration: ${avgDuration.toFixed(4)}ms per event`);

    expect(avgDuration).toBeLessThan(10);
  });
});
