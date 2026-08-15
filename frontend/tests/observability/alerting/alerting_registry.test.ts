import { describe, it, expect } from 'vitest';
import {
  AlertRegistry,
  AlertValidationError,
  AlertNotFoundError,
  createAlertRecord
} from '../../../src/observability';

describe('AlertRegistry Tests', () => {
  it('1. should register alerts and list them in deterministic insertion order', () => {
    const registry = new AlertRegistry();

    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const a2 = createAlertRecord({
      id: 'alert-2',
      sourceId: 'src-2',
      severity: 'WARNING',
      state: 'ACTIVE',
      title: 'Alert 2',
      message: 'Msg 2',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    registry.registerAlert(a2);

    const alerts = registry.listAlerts();
    expect(alerts).toHaveLength(2);
    expect(alerts[0].id).toBe('alert-1');
    expect(alerts[1].id).toBe('alert-2');
  });

  it('2. should reject duplicate alert IDs', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    expect(() => registry.registerAlert(a1)).toThrow(AlertValidationError);
  });

  it('3. should lookup alerts in O(1) conceptually', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    expect(registry.getAlert('alert-1')).toBeDefined();
    expect(registry.getAlert('alert-missing')).toBeNull();
  });

  it('4. should handle missing alerts on removal', () => {
    const registry = new AlertRegistry();
    expect(() => registry.removeAlert('missing')).toThrow(AlertNotFoundError);
  });

  it('5. should support removal and clear operations', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });
    const a2 = createAlertRecord({
      id: 'alert-2',
      sourceId: 'src-2',
      severity: 'WARNING',
      state: 'ACTIVE',
      title: 'Alert 2',
      message: 'Msg 2',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    registry.registerAlert(a2);

    registry.removeAlert('alert-1');
    expect(registry.listAlerts()).toHaveLength(1);
    expect(registry.listAlerts()[0].id).toBe('alert-2');

    registry.clear();
    expect(registry.listAlerts()).toHaveLength(0);
  });

  it('6. should register rules and list them in deterministic insertion order', () => {
    const registry = new AlertRegistry();
    const cond = { id: 'c1', field: 'f1', operator: 'EQ' as const, expectedValue: 1 };
    const group = { operator: 'ALL' as const, conditions: [cond] };

    const r1 = {
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc 1',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: group,
      sourceId: 'src-1',
      tags: ['tag1'],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    const r2 = {
      id: 'rule-2',
      name: 'Rule 2',
      description: 'Desc 2',
      enabled: false,
      severity: 'WARNING' as const,
      conditions: group,
      sourceId: 'src-2',
      tags: ['tag2'],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    registry.registerRule(r1);
    registry.registerRule(r2);

    const rules = registry.listRules();
    expect(rules).toHaveLength(2);
    expect(rules[0].id).toBe('rule-1');
    expect(rules[1].id).toBe('rule-2');
  });

  it('7. should reject duplicate rule IDs', () => {
    const registry = new AlertRegistry();
    const cond = { id: 'c1', field: 'f1', operator: 'EQ' as const, expectedValue: 1 };
    const group = { operator: 'ALL' as const, conditions: [cond] };

    const r1 = {
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc 1',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: group,
      sourceId: 'src-1',
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    registry.registerRule(r1);
    expect(() => registry.registerRule(r1)).toThrow();
  });

  it('8. should support rule lookup and state checking', () => {
    const registry = new AlertRegistry();
    const cond = { id: 'c1', field: 'f1', operator: 'EQ' as const, expectedValue: 1 };
    const group = { operator: 'ALL' as const, conditions: [cond] };

    const r1 = {
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc 1',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: group,
      sourceId: 'src-1',
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    registry.registerRule(r1);
    expect(registry.hasRule('rule-1')).toBe(true);
    expect(registry.hasRule('rule-missing')).toBe(false);
    expect(registry.getRule('rule-1')!.name).toBe('Rule 1');
    expect(registry.getRule('rule-missing')).toBeNull();
  });

  it('9. should support updating existing rules and reject unknown updates', () => {
    const registry = new AlertRegistry();
    const cond = { id: 'c1', field: 'f1', operator: 'EQ' as const, expectedValue: 1 };
    const group = { operator: 'ALL' as const, conditions: [cond] };

    const r1 = {
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc 1',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: group,
      sourceId: 'src-1',
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    registry.registerRule(r1);

    const updatedRule = { ...r1, name: 'Updated Rule Name' };
    registry.updateRule(updatedRule);
    expect(registry.getRule('rule-1')!.name).toBe('Updated Rule Name');

    const unknownRule = { ...r1, id: 'rule-unknown' };
    expect(() => registry.updateRule(unknownRule)).toThrow();
  });

  it('10. should support rule unregistration and clear', () => {
    const registry = new AlertRegistry();
    const cond = { id: 'c1', field: 'f1', operator: 'EQ' as const, expectedValue: 1 };
    const group = { operator: 'ALL' as const, conditions: [cond] };

    const r1 = {
      id: 'rule-1',
      name: 'Rule 1',
      description: 'Desc 1',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: group,
      sourceId: 'src-1',
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    registry.registerRule(r1);
    expect(registry.listRules()).toHaveLength(1);

    expect(() => registry.unregisterRule('rule-missing')).toThrow();

    registry.unregisterRule('rule-1');
    expect(registry.listRules()).toHaveLength(0);

    registry.registerRule(r1);
    registry.clearRules();
    expect(registry.listRules()).toHaveLength(0);
  });
});
