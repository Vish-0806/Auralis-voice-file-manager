import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  AlertingProvider,
  AlertingRuntime,
  AlertRule,
  AlertEvaluationContext,
  AlertOrchestrationRequest,
  InMemoryNotificationChannel,
  AlertSuppressionPolicy,
  AlertMaintenanceWindow
} from '../../../src/observability';

// Helper provider that overrides generated alert ID to match snoozing targets
class DeterministicAlertProvider extends AlertingProvider {
  public override generateAlert(rule: any, evaluationResult: any): any {
    const alert = super.generateAlert(rule, evaluationResult);
    this.removeAlert(alert.id);
    const deterministicAlert = {
      ...alert,
      id: 'alert-rule-cpu'
    };
    this.registerAlert(deterministicAlert);
    return deterministicAlert;
  }
}

describe('Alerting Orchestration Runtime Tests', () => {
  let provider: AlertingProvider;
  let runtime: AlertingRuntime;
  let testRule: AlertRule;
  let testContext: AlertEvaluationContext;
  let recipient: any;

  beforeEach(async () => {
    provider = new AlertingProvider();
    runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    testRule = {
      id: 'rule-cpu',
      name: 'High CPU Usage',
      description: 'High CPU usage detected',
      sourceId: 'src-cpu',
      version: 1,
      enabled: true,
      severity: 'ERROR',
      conditions: {
        operator: 'ALL',
        conditions: [
          {
            id: 'c1',
            field: 'cpu_usage',
            operator: 'GT',
            expectedValue: 90
          }
        ]
      },
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    testContext = {
      values: {
        cpu_usage: 95
      }
    };

    recipient = {
      id: 'recip-1',
      name: 'System Admin',
      address: 'admin@auralis.io'
    };

    runtime.registerRule(testRule);
  });

  afterEach(async () => {
    await runtime.shutdown();
  });

  it('1. Successful end-to-end orchestration', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-success',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await runtime.orchestrate(request);
    expect(result.status).toBe('SUCCESS');
    expect(result.stageResults).toHaveLength(6);
    expect(result.alertId).toBeDefined();
    expect(result.fingerprint).toBeDefined();

    const stats = runtime.getStatistics();
    expect(stats.orchestrationsTotal).toBe(1);
    expect(stats.orchestrationsSuccessful).toBe(1);

    expect(runtime.getResult('orch-success')).toEqual(result);
  });

  it('2. Non-matching rule evaluation skips generation and dispatch', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const lowCpuContext: AlertEvaluationContext = {
      values: { cpu_usage: 50 }
    };

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-skip',
      ruleId: 'rule-cpu',
      context: lowCpuContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await runtime.orchestrate(request);
    expect(result.status).toBe('SKIPPED');
    expect(result.alertId).toBeUndefined();
    expect(result.stageResults).toHaveLength(1);
    expect(result.stageResults[0].status).toBe('SKIPPED');

    const stats = runtime.getStatistics();
    expect(stats.orchestrationsSkipped).toBe(1);
  });

  it('3. Duplicate alert deduplication/cooldown skips suppression and notifications', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const req1: AlertOrchestrationRequest = {
      orchestrationId: 'orch-dup-1',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result1 = await runtime.orchestrate(req1);
    expect(result1.status).toBe('SUCCESS');

    const req2: AlertOrchestrationRequest = {
      orchestrationId: 'orch-dup-2',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result2 = await runtime.orchestrate(req2);
    expect(result2.status).toBe('DUPLICATE');
    expect(result2.stageResults[2].status).toBe('DUPLICATE');
    expect(result2.stageResults).toHaveLength(3);
  });

  it('4. Suppressed policy evaluation halts delivery', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const policy: AlertSuppressionPolicy = {
      id: 'supp-policy-1',
      name: 'Suppress CPU alerts',
      enabled: true,
      priority: 10,
      scope: 'RULE',
      ruleId: 'rule-cpu',
      reason: 'POLICY'
    };
    runtime.registerSuppressionPolicy(policy);

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-suppressed',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await runtime.orchestrate(request);
    expect(result.status).toBe('SUPPRESSED');
    expect(result.stageResults[3].status).toBe('SUPPRESSED');
    expect(result.stageResults).toHaveLength(4);
  });

  it('5. Active maintenance window evaluation halts delivery', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const now = Date.now();
    const window: AlertMaintenanceWindow = {
      id: 'maint-1',
      name: 'Weekly Maintenance',
      enabled: true,
      startTime: now - 1000,
      endTime: now + 5000,
      reason: 'DB patching'
    };
    runtime.registerMaintenanceWindow(window);

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-maint',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await runtime.orchestrate(request);
    expect(result.status).toBe('SUPPRESSED');
    expect(result.suppressionDecision?.reason).toBe('MAINTENANCE');
  });

  it('6. Alert snoozing evaluation halts delivery', async () => {
    // Instantiate with DeterministicAlertProvider
    const customProvider = new DeterministicAlertProvider();
    const customRuntime = new AlertingRuntime(customProvider);
    await customRuntime.initialize();
    customRuntime.registerRule(testRule);

    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    customRuntime.registerNotificationChannel(channel);

    // Register snooze on the deterministic ID
    customRuntime.snoozeAlert('alert-rule-cpu', undefined, 10000, 'USER', 'Snoozed alert');

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-snoozed',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await customRuntime.orchestrate(request);
    expect(result.status).toBe('SUPPRESSED');
    expect(result.suppressionDecision?.reason).toBe('SNOOZED');

    await customRuntime.shutdown();
  });

  it('7. Concurrency Promise sharing checks', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-concurrent',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const p1 = runtime.orchestrate(request);
    const p2 = runtime.orchestrate(request);

    expect(p1).toBe(p2);

    const r1 = await p1;
    const r2 = await p2;
    expect(r1).toBe(r2);
  });

  it('8. Batch orchestration', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    runtime.registerNotificationChannel(channel);

    const reqs: AlertOrchestrationRequest[] = [
      {
        orchestrationId: 'batch-1',
        ruleId: 'rule-cpu',
        context: testContext,
        channelId: 'ch-email-1',
        recipient,
        priority: 'HIGH',
        channelType: 'EMAIL'
      },
      {
        orchestrationId: 'batch-2',
        ruleId: 'rule-cpu',
        context: { values: { cpu_usage: 10 } },
        channelId: 'ch-email-1',
        recipient,
        priority: 'HIGH',
        channelType: 'EMAIL'
      }
    ];

    const results = await runtime.orchestrateMany(reqs);
    expect(results).toHaveLength(2);
    expect(results[0].status).toBe('SUCCESS');
    expect(results[1].status).toBe('SKIPPED');
  });

  it('9. Preserves alert and lifecycle after notification failure', async () => {
    const channel = new InMemoryNotificationChannel('ch-email-1', 'Email Channel');
    channel.simulateFailures(3); // Exceed default max attempts (3) to verify failure
    runtime.registerNotificationChannel(channel);

    const request: AlertOrchestrationRequest = {
      orchestrationId: 'orch-notif-fail',
      ruleId: 'rule-cpu',
      context: testContext,
      channelId: 'ch-email-1',
      recipient,
      priority: 'HIGH',
      channelType: 'EMAIL'
    };

    const result = await runtime.orchestrate(request);
    expect(result.status).toBe('COMPLETED');
    expect(result.stageResults[5].status).toBe('FAILED');

    const alertId = result.alertId;
    expect(alertId).toBeDefined();
    expect(runtime.getAlert(alertId!)).toBeDefined();
    expect(runtime.getAlertLifecycle(alertId!)?.state).toBe('ACTIVE');
  });
});
