import { describe, it, expect } from 'vitest';
import {
  createRuleCondition,
  createConditionGroup,
  createAlertRule,
  AlertRuleValidationError
} from '../../../src/observability';

describe('Alerting Factories & Validation Tests', () => {
  it('1. should create valid conditions and reject invalid inputs', () => {
    const cond = createRuleCondition({
      id: 'cond-1',
      field: 'cpu.usage',
      operator: 'GT',
      expectedValue: 90
    });

    expect(cond.id).toBe('cond-1');
    expect(cond.field).toBe('cpu.usage');
    expect(cond.operator).toBe('GT');
    expect(cond.expectedValue).toBe(90);

    // Reject empty ID
    expect(() => createRuleCondition({
      id: '',
      field: 'cpu.usage',
      operator: 'GT'
    })).toThrow(AlertRuleValidationError);

    // Reject empty field
    expect(() => createRuleCondition({
      id: 'cond-2',
      field: '',
      operator: 'GT'
    })).toThrow(AlertRuleValidationError);

    // Reject invalid operator
    expect(() => createRuleCondition({
      id: 'cond-2',
      field: 'cpu.usage',
      operator: 'INVALID_OP' as any
    })).toThrow(AlertRuleValidationError);
  });

  it('2. should create valid condition groups and validate logical nesting', () => {
    const cond1 = createRuleCondition({
      id: 'c1',
      field: 'mem.usage',
      operator: 'GTE',
      expectedValue: 85
    });

    const group = createConditionGroup({
      operator: 'ALL',
      conditions: [cond1]
    });

    expect(group.operator).toBe('ALL');
    expect(group.conditions).toHaveLength(1);
    expect(group.conditions[0]).toStrictEqual(cond1);

    // Reject invalid operator
    expect(() => createConditionGroup({
      operator: 'XOR' as any,
      conditions: [cond1]
    })).toThrow(AlertRuleValidationError);

    // Reject empty conditions list
    expect(() => createConditionGroup({
      operator: 'ANY',
      conditions: []
    })).toThrow(AlertRuleValidationError);
  });

  it('3. should enforce nesting depth limit (recursion limit) to prevent stack overflow', () => {
    const cond = createRuleCondition({ id: 'c', field: 'f', operator: 'EQ', expectedValue: 1 });
    
    // Create nested groups of depth 12
    let currentGroup: any = cond;
    for (let i = 0; i < 12; i++) {
      currentGroup = {
        operator: 'ALL',
        conditions: [currentGroup]
      };
    }

    // Try creating rule with this deeply nested group, should reject
    expect(() => createAlertRule({
      id: 'rule-deep',
      name: 'Deep Rule',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: currentGroup,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    })).toThrow(AlertRuleValidationError);
  });

  it('4. should reject duplicate condition IDs within a rule', () => {
    const cond1 = createRuleCondition({ id: 'dup-id', field: 'f1', operator: 'EQ', expectedValue: 1 });
    const cond2 = createRuleCondition({ id: 'dup-id', field: 'f2', operator: 'EQ', expectedValue: 2 });

    const group = createConditionGroup({
      operator: 'ANY',
      conditions: [cond1, cond2]
    });

    expect(() => createAlertRule({
      id: 'rule-dup-cond',
      name: 'Dup Cond Rule',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    })).toThrow(AlertRuleValidationError);
  });

  it('5. should reject invalid severity, timestamps, versions, etc. in alert rules', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'f1', operator: 'EQ', expectedValue: 1 });
    const group = createConditionGroup({ operator: 'ALL', conditions: [cond] });

    // Invalid Severity
    expect(() => createAlertRule({
      id: 'r1',
      name: 'Rule 1',
      description: 'Desc',
      enabled: true,
      severity: 'SUPER_CRITICAL' as any,
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    })).toThrow(AlertRuleValidationError);

    // Invalid Timestamps
    expect(() => createAlertRule({
      id: 'r1',
      name: 'Rule 1',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: -100,
      updatedAt: Date.now()
    })).toThrow(AlertRuleValidationError);

    // Invalid version
    expect(() => createAlertRule({
      id: 'r1',
      name: 'Rule 1',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      version: -1
    })).toThrow(AlertRuleValidationError);
  });
});
