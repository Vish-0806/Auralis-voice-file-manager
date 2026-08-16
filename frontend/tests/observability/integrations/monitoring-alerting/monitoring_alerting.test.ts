import { describe, it, expect, vi } from 'vitest';
import {
  MonitoringAlertingRuntime,
  MonitoringAlertingProvider,
  MonitoringAlertingStateError,
  MonitoringAlertingPolicyError,
  MonitorStatus
} from '../../../../src/observability';
import { MonitoringResult } from '../../../../src/observability/models/monitoring';

// Helper to construct fully stubbed mock Alerting Runtime
const createMockAlertingRuntime = () => {
  return {
    initialize: vi.fn(async () => {}),
    shutdown: vi.fn(async () => {}),
    getState: vi.fn(() => 'READY'),
    orchestrate: vi.fn(async (req) => {
      if (req.ruleId === 'failing-rule') {
        throw new Error('Alerting Engine Crash');
      }
      return {
        orchestrationId: req.orchestrationId,
        ruleId: req.ruleId,
        status: req.ruleId === 'suppressed-rule' ? 'SUPPRESSED' : 'SUCCESS',
        stageResults: [],
        attemptedAt: Date.now(),
        completedAt: Date.now(),
        duration: 2
      };
    })
  } as any;
};

// Helper to construct fully stubbed mock Correlation Runtime
const createMockCorrelationRuntime = () => {
  return {
    initialize: vi.fn(async () => {}),
    shutdown: vi.fn(async () => {}),
    getState: vi.fn(() => 'READY'),
    createContext: vi.fn((opts) => ({
      correlationId: 'corr_test_generated',
      timestamp: Date.now(),
      ...opts
    }))
  } as any;
};

describe('Monitoring Alerting Integration Tests', () => {
  it('1. Construction, DI, and Initial State', () => {
    const alerting = createMockAlertingRuntime();
    const correlation = createMockCorrelationRuntime();

    // DI Construction
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: alerting,
      correlationRuntime: correlation
    });
    expect(provider.getState()).toBe('UNINITIALIZED');
    expect(provider.getHealth()).toBe('UNKNOWN');

    // Runtime Coordinator DI wrapper
    const runtime = new MonitoringAlertingRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  it('2. Initialization & shutdown lifecycles (idempotency, concurrency)', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });

    const p1 = provider.initialize();
    const p2 = provider.initialize();
    expect(p1).toBe(p2); // Promise Caching
    await p1;

    expect(provider.getState()).toBe('READY');
    expect(provider.getHealth()).toBe('HEALTHY');

    // Idempotent initialize
    await provider.initialize();

    const p3 = provider.shutdown();
    const p4 = provider.shutdown();
    expect(p3).toBe(p4); // Promise Caching
    await p3;

    expect(provider.getState()).toBe('STOPPED');

    // Idempotent shutdown
    await provider.shutdown();
  });

  it('3. Policy registration, duplicate rejection, and lookup', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });
    await provider.initialize();

    const policy = {
      id: 'p-1',
      enabled: true,
      componentId: 'subsystem-x',
      ruleId: 'alert-rule-100'
    };

    provider.registerPolicy(policy);
    expect(provider.getPolicy('p-1')).toEqual(policy);

    // Duplicate ID rejection
    expect(() => provider.registerPolicy(policy)).toThrow(
      MonitoringAlertingPolicyError
    );

    // Enable/Disable
    provider.disablePolicy('p-1');
    expect(provider.getPolicy('p-1')?.enabled).toBe(false);

    provider.enablePolicy('p-1');
    expect(provider.getPolicy('p-1')?.enabled).toBe(true);

    // Unregister
    provider.unregisterPolicy('p-1');
    expect(provider.getPolicy('p-1')).toBeNull();
  });

  it('4. Specific policy matching precedence', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });
    await provider.initialize();

    // 1. Global policy
    provider.registerPolicy({
      id: 'policy-global',
      enabled: true,
      ruleId: 'rule-global'
    });

    // 2. Component specific policy
    provider.registerPolicy({
      id: 'policy-comp',
      enabled: true,
      componentId: 'comp-1',
      ruleId: 'rule-comp'
    });

    // 3. Check specific policy
    provider.registerPolicy({
      id: 'policy-check',
      enabled: true,
      componentId: 'comp-1',
      checkId: 'check-1',
      ruleId: 'rule-check'
    });

    const list = provider.listPolicies();

    // Match candidate check-specific
    const resCheck: MonitoringResult = {
      componentId: 'comp-1',
      checkId: 'check-1',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 10
    };
    const { findMatchingPolicy } = await import(
      '../../../../src/observability/integrations/monitoring-alerting/MonitoringAlertingAdapter'
    );
    expect(findMatchingPolicy(list, resCheck)?.ruleId).toBe('rule-check');

    // Match candidate component-specific
    const resComp: MonitoringResult = {
      componentId: 'comp-1',
      checkId: 'check-other',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };
    expect(findMatchingPolicy(list, resComp)?.ruleId).toBe('rule-comp');

    // Match candidate global
    const resGlobal: MonitoringResult = {
      componentId: 'comp-other',
      checkId: 'check-other',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };
    expect(findMatchingPolicy(list, resGlobal)?.ruleId).toBe('rule-global');
  });

  it('5. Integration outcomes: trigger evaluation and recovery transition rules', async () => {
    const alerting = createMockAlertingRuntime();
    const correlation = createMockCorrelationRuntime();
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: alerting,
      correlationRuntime: correlation
    });
    await provider.initialize();

    provider.registerPolicy({
      id: 'policy-1',
      enabled: true,
      componentId: 'service-a',
      ruleId: 'alert-rule-1'
    });

    // 1. HEALTHY status should not trigger rule matches on first evaluation (since there is no state transition)
    const resultHealthy: MonitoringResult = {
      componentId: 'service-a',
      checkId: '',
      status: MonitorStatus.HEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };

    let intResult = await provider.processResult(resultHealthy);
    expect(intResult.occurred).toBe(true); // Matches and delegates HEALTHY to check for recovery
    expect(intResult.skipped).toBe(false);

    // 2. UNHEALTHY should trigger rule matched delegation
    const resultUnhealthy: MonitoringResult = {
      componentId: 'service-a',
      checkId: '',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };

    intResult = await provider.processResult(resultUnhealthy);
    expect(intResult.occurred).toBe(true);
    expect(intResult.skipped).toBe(false);
    expect(alerting.orchestrate).toHaveBeenCalledTimes(2);

    // 3. Repeat of same UNHEALTHY status without change must be skipped (state transition awareness)
    intResult = await provider.processResult(resultUnhealthy);
    expect(intResult.occurred).toBe(false);
    expect(intResult.skipped).toBe(true);
    expect(intResult.reason).toContain('remains unchanged');

    // 4. Recovery transition: UNHEALTHY -> HEALTHY should propagate to allow alert engine to resolve alert
    intResult = await provider.processResult(resultHealthy);
    expect(intResult.occurred).toBe(true); // Propagated for recovery resolution
    expect(intResult.skipped).toBe(false);
  });

  it('6. Correlation context preservation & generation', async () => {
    const correlation = createMockCorrelationRuntime();
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: correlation
    });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p',
      enabled: true,
      componentId: 'comp',
      ruleId: 'rule'
    });

    // Case A: Correlation context already exists in result details
    const resWithCorr: MonitoringResult = {
      componentId: 'comp',
      checkId: '',
      status: MonitorStatus.DEGRADED,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 1,
      details: { correlationId: 'existing-correlation-id-999' }
    };

    let result = await provider.processResult(resWithCorr);
    expect(result.correlationId).toBe('existing-correlation-id-999');

    // Case B: No context exists -> generates a new one via correlation runtime
    const resWithoutCorr: MonitoringResult = {
      componentId: 'comp',
      checkId: '',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 1
    };

    result = await provider.processResult(resWithoutCorr);
    expect(result.correlationId).toBe('corr_test_generated');
    expect(correlation.createContext).toHaveBeenCalled();
  });

  it('7. Duplicate concurrent processing protection', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p',
      enabled: true,
      componentId: 'comp-dup',
      ruleId: 'rule'
    });

    const res: MonitoringResult = {
      componentId: 'comp-dup',
      checkId: '',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };

    const p1 = provider.processResult(res);
    const p2 = provider.processResult(res);

    expect(p1).toBe(p2); // Duplicate concurrent requests mapped to same promise
    await p1;

    expect(provider.getStatistics().duplicateIntegrationRequests).toBe(1);
  });

  it('8. Failure isolation: Alerting Runtime crash', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });
    await provider.initialize();

    provider.registerPolicy({
      id: 'p',
      enabled: true,
      componentId: 'comp-fail',
      ruleId: 'failing-rule'
    });

    const res: MonitoringResult = {
      componentId: 'comp-fail',
      checkId: '',
      status: MonitorStatus.UNHEALTHY,
      startedAt: Date.now(),
      completedAt: Date.now(),
      durationMs: 5
    };

    // Alerting failure is isolated and does not crash the call flow
    const integrationResult = await provider.processResult(res);
    expect(integrationResult.occurred).toBe(false);
    expect(integrationResult.skipped).toBe(false);
    expect(integrationResult.reason).toContain('Integration failed');

    // Statistics & Diagnostics verification
    const stats = provider.getStatistics();
    expect(stats.failedAlertingRequests).toBe(1);
    expect(stats.integrationErrors).toBe(1);

    const diags = provider.getDiagnostics();
    expect(diags.recentFailures.length).toBe(1);
    expect(diags.recentFailures[0].error.message).toContain('Alerting Engine Crash');
    expect(Object.isFrozen(diags)).toBe(true); // Immutability
  });

  it('9. Lifecycle transition constraints', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });

    (provider as any)._state = 'STOPPING';

    await expect(provider.initialize()).rejects.toThrow(
      MonitoringAlertingStateError
    );
  });

  it('10. Data hygiene: redacting sensitive data in metadata', async () => {
    const provider = new MonitoringAlertingProvider({
      alertingRuntime: createMockAlertingRuntime(),
      correlationRuntime: createMockCorrelationRuntime()
    });
    await provider.initialize();

    // Registering policy containing metadata with sensitive keys
    provider.registerPolicy({
      id: 'p-sensitive',
      enabled: true,
      componentId: 'comp-sensitive',
      ruleId: 'rule-xyz',
      metadata: {
        password: '123',
        secret_key: 'abc'
      }
    });

    const policy = provider.getPolicy('p-sensitive');
    expect(policy?.metadata?.password).toBe('[REDACTED]');
    expect(policy?.metadata?.secret_key).toBe('[REDACTED]');
  });
});
