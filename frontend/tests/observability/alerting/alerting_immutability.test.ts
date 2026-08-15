import { describe, it, expect } from 'vitest';
import {
  AlertingProvider,
  createAlertRecord,
  createAlertRule,
  createRuleCondition,
  createConditionGroup
} from '../../../src/observability';

describe('Alerting Immutability & Defensive Snapshots Tests', () => {
  it('1. returned AlertRecord and metadata must be frozen', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();

    const alert = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: { key: 'value' }
    });

    // Factory should return a frozen record
    expect(Object.isFrozen(alert)).toBe(true);
    expect(Object.isFrozen(alert.metadata)).toBe(true);

    provider.registerAlert(alert);

    // Registry / Provider retrieval must return a frozen copy
    const retrieved = provider.getAlert('alert-1')!;
    expect(Object.isFrozen(retrieved)).toBe(true);
    expect(Object.isFrozen(retrieved.metadata)).toBe(true);

    // Mutating should throw in strict mode
    expect(() => {
      (retrieved as any).title = 'Mutated Title';
    }).toThrow();

    expect(() => {
      (retrieved.metadata as any).key = 'mutated';
    }).toThrow();
  });

  it('2. listAlerts returned array must be frozen', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();

    const alert = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    provider.registerAlert(alert);
    const list = provider.listAlerts();

    expect(Object.isFrozen(list)).toBe(true);
    expect(() => {
      (list as any).push(alert);
    }).toThrow();
  });

  it('3. statistics and diagnostics must be frozen', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();

    const stats = provider.getStatistics();
    const diags = provider.getDiagnostics();

    expect(Object.isFrozen(stats)).toBe(true);
    expect(Object.isFrozen(diags)).toBe(true);

    expect(() => {
      (stats as any).registeredAlertCount = 100;
    }).toThrow();

    expect(() => {
      (diags as any).runtimeState = 'STOPPED';
    }).toThrow();
  });

  it('4. alert rule and condition group must be frozen', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();

    const cond = createRuleCondition({
      id: 'cond-1',
      field: 'cpu',
      operator: 'GT',
      expectedValue: 80,
      metadata: { limit: '80%' }
    });

    const group = createConditionGroup({
      operator: 'ALL',
      conditions: [cond]
    });

    const rule = createAlertRule({
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      tags: ['tag1'],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: { env: 'prod' }
    });

    expect(Object.isFrozen(rule)).toBe(true);
    expect(Object.isFrozen(rule.conditions)).toBe(true);
    expect(Object.isFrozen(rule.conditions.conditions)).toBe(true);
    expect(Object.isFrozen(rule.tags)).toBe(true);
    expect(Object.isFrozen(rule.metadata)).toBe(true);

    provider.registerRule(rule);

    const retrieved = provider.getRule('rule-1')!;
    expect(Object.isFrozen(retrieved)).toBe(true);
    expect(Object.isFrozen(retrieved.conditions)).toBe(true);

    expect(() => {
      (retrieved as any).name = 'mutate';
    }).toThrow();

    const rulesList = provider.listRules();
    expect(Object.isFrozen(rulesList)).toBe(true);
    expect(() => {
      (rulesList as any).push(rule);
    }).toThrow();
  });
});
