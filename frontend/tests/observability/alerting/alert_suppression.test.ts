import { describe, it, expect } from 'vitest';
import {
  AlertSuppressionManager,
  AlertingProvider,
  AlertingRuntime,
  AlertSuppressionPolicyError,
  createAlertRecord
} from '../../../src/observability';

describe('Alert Suppression Manager Tests', () => {
  const manager = new AlertSuppressionManager();

  const mockAlert = createAlertRecord({
    id: 'alert-1',
    sourceId: 'src-1',
    severity: 'ERROR',
    state: 'ACTIVE',
    title: 'Alert 1',
    message: 'Message 1',
    createdAt: 1000,
    updatedAt: 1000,
    metadata: {}
  });

  const alertWithRuleAndFp = {
    ...mockAlert,
    ruleId: 'rule-1',
    fingerprint: 'fp-1'
  };

  it('1. Policy registration, duplicate rejection, and removal', () => {
    manager.clearAll();
    const policy = {
      id: 'p-1',
      name: 'Disable system CPU alerts',
      enabled: true,
      priority: 10,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'DISABLED' as const
    };

    manager.registerPolicy(policy);
    expect(manager.listPolicies()).toHaveLength(1);

    expect(() => manager.registerPolicy(policy)).toThrow(AlertSuppressionPolicyError);

    manager.unregisterPolicy('p-1');
    expect(manager.listPolicies()).toHaveLength(0);
  });

  it('2. Policy validation', () => {
    expect(() =>
      manager.registerPolicy({
        id: '',
        name: 'Empty ID policy',
        enabled: true,
        priority: 1,
        scope: 'GLOBAL' as const,
        reason: 'MAINTENANCE' as const
      })
    ).toThrow(AlertSuppressionPolicyError);
  });

  it('3. Maintenance window registration, validation, active boundaries, and expiration', () => {
    manager.clearAll();
    const mw = {
      id: 'mw-1',
      name: 'System Patching',
      enabled: true,
      startTime: 2000,
      endTime: 5000,
      reason: 'Scheduled maintenance'
    };

    manager.registerMaintenanceWindow(mw);
    expect(manager.listMaintenanceWindows()).toHaveLength(1);

    const decBefore = manager.evaluateSuppression(alertWithRuleAndFp, 1999);
    expect(decBefore.suppressed).toBe(false);

    const decStart = manager.evaluateSuppression(alertWithRuleAndFp, 2000);
    expect(decStart.suppressed).toBe(true);
    expect(decStart.reason).toBe('MAINTENANCE');

    const decMiddle = manager.evaluateSuppression(alertWithRuleAndFp, 3000);
    expect(decMiddle.suppressed).toBe(true);

    const decEnd = manager.evaluateSuppression(alertWithRuleAndFp, 5000);
    expect(decEnd.suppressed).toBe(false);
  });

  it('4. Snoozing creation, active lookup, and expiration', () => {
    manager.clearAll();
    manager.snoozeAlert('alert-1', 'fp-1', 3000, 'USER', 'Checking DB CPU logs', {}, 1000);

    expect(manager.getSnooze('alert-1')).toBeDefined();

    expect(manager.isSnoozed('alert-1', 2000)).toBe(true);
    expect(manager.evaluateSuppression(alertWithRuleAndFp, 2000).suppressed).toBe(true);

    expect(manager.isSnoozed('alert-1', 4000)).toBe(false);
    expect(manager.evaluateSuppression(alertWithRuleAndFp, 4000).suppressed).toBe(false);

    manager.clearSnooze('alert-1');
    expect(manager.getSnooze('alert-1')).toBeNull();
  });

  it('5. Precedence scopes and priorities evaluation', () => {
    manager.clearAll();

    manager.registerMaintenanceWindow({
      id: 'mw-1',
      name: 'Maintenance',
      enabled: true,
      startTime: 1000,
      endTime: 5000,
      reason: 'Server upgrade'
    });
    manager.registerPolicy({
      id: 'p-global',
      name: 'Global policy',
      enabled: true,
      priority: 1,
      scope: 'GLOBAL' as const,
      reason: 'DISABLED' as const
    });

    const dec1 = manager.evaluateSuppression(alertWithRuleAndFp, 2000);
    expect(dec1.suppressed).toBe(true);
    expect(dec1.reason).toBe('MAINTENANCE');

    manager.registerPolicy({
      id: 'p-rule',
      name: 'Rule policy',
      enabled: true,
      priority: 5,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'POLICY' as const
    });

    const dec2 = manager.evaluateSuppression(alertWithRuleAndFp, 2000);
    expect(dec2.suppressed).toBe(true);
    expect(dec2.reason).toBe('POLICY');
    expect(dec2.policyId).toBe('p-rule');

    manager.snoozeAlert('alert-1', 'fp-1', 4000, 'USER', 'Debug snooze', {}, 1000);
    const dec3 = manager.evaluateSuppression(alertWithRuleAndFp, 2000);
    expect(dec3.suppressed).toBe(true);
    expect(dec3.reason).toBe('SNOOZED');
  });

  it('6. Priority and alphabetical tie-breaking rules', () => {
    manager.clearAll();

    manager.registerPolicy({
      id: 'p-low',
      name: 'Low priority rule policy',
      enabled: true,
      priority: 5,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'POLICY' as const
    });
    manager.registerPolicy({
      id: 'p-high',
      name: 'High priority rule policy',
      enabled: true,
      priority: 10,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'DISABLED' as const
    });

    const dec1 = manager.evaluateSuppression(alertWithRuleAndFp, 1000);
    expect(dec1.policyId).toBe('p-high');
    expect(dec1.reason).toBe('DISABLED');

    manager.registerPolicy({
      id: 'p-b',
      name: 'B rule policy',
      enabled: true,
      priority: 10,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'RATE_LIMITED' as const
    });
    manager.registerPolicy({
      id: 'p-a',
      name: 'A rule policy',
      enabled: true,
      priority: 10,
      scope: 'RULE' as const,
      ruleId: 'rule-1',
      reason: 'POLICY' as const
    });

    const dec2 = manager.evaluateSuppression(alertWithRuleAndFp, 1000);
    expect(dec2.policyId).toBe('p-a');
    expect(dec2.reason).toBe('POLICY');
  });

  it('7. Statistics and diagnostics counters', () => {
    manager.clearAll();
    manager.registerPolicy({
      id: 'p-global',
      name: 'Global policy',
      enabled: true,
      priority: 1,
      scope: 'GLOBAL' as const,
      reason: 'DISABLED' as const
    });

    manager.evaluateSuppression(alertWithRuleAndFp, 1000);
    manager.evaluateSuppression(alertWithRuleAndFp, 1000);

    const stats = manager.getStats();
    expect(stats.suppressionEvaluations).toBe(2);
    expect(stats.suppressedAlerts).toBe(2);
    expect(stats.policyMatches).toBe(2);

    const diagnostics = manager.getDiagnostics(Date.now());
    expect(diagnostics.registeredPoliciesCount).toBe(1);
    expect(diagnostics.enabledPoliciesCount).toBe(1);
    expect(diagnostics.historySize).toBe(2);
  });

  it('8. Provider and Runtime delegation', async () => {
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    runtime.registerSuppressionPolicy({
      id: 'p-global',
      name: 'Global',
      enabled: true,
      priority: 1,
      scope: 'GLOBAL' as const,
      reason: 'DISABLED' as const
    });

    expect(runtime.listSuppressionPolicies()).toHaveLength(1);

    const decision = runtime.evaluateSuppression(alertWithRuleAndFp, 1000);
    expect(decision.suppressed).toBe(true);
    expect(decision.reason).toBe('DISABLED');
  });
});
