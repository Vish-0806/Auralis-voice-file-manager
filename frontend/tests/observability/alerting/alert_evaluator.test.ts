import { describe, it, expect } from 'vitest';
import {
  AlertEvaluator,
  AlertingProvider,
  AlertingRuntime,
  createAlertRule,
  createRuleCondition,
  createConditionGroup
} from '../../../src/observability';

describe('AlertEvaluator Tests', () => {
  const evaluator = new AlertEvaluator();

  it('1. EQ operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'EQ', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res1.matched).toBe(true);
    expect(res1.status).toBe('MATCHED');

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 200 } });
    expect(res2.matched).toBe(false);
    expect(res2.status).toBe('NOT_MATCHED');
  });

  it('2. NEQ operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'NEQ', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 200 } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res2.matched).toBe(false);
  });

  it('3. GT operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'GT', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 150 } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res2.matched).toBe(false);

    const res3 = evaluator.evaluateCondition(cond, { values: { val: 50 } });
    expect(res3.matched).toBe(false);
  });

  it('4. GTE operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'GTE', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 50 } });
    expect(res2.matched).toBe(false);
  });

  it('5. LT operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'LT', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 50 } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res2.matched).toBe(false);
  });

  it('6. LTE operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'LTE', expectedValue: 100 });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 100 } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 150 } });
    expect(res2.matched).toBe(false);
  });

  it('7. CONTAINS logic (string and array)', () => {
    // String contains
    const condStr = createRuleCondition({ id: 'c1', field: 'msg', operator: 'CONTAINS', expectedValue: 'hello' });
    const res1 = evaluator.evaluateCondition(condStr, { values: { msg: 'say hello world' } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(condStr, { values: { msg: 'say goodbye' } });
    expect(res2.matched).toBe(false);

    // Array contains
    const condArr = createRuleCondition({ id: 'c2', field: 'list', operator: 'CONTAINS', expectedValue: 'admin' });
    const res3 = evaluator.evaluateCondition(condArr, { values: { list: ['user', 'admin', 'guest'] } });
    expect(res3.matched).toBe(true);

    const res4 = evaluator.evaluateCondition(condArr, { values: { list: ['user', 'guest'] } });
    expect(res4.matched).toBe(false);
  });

  it('8. NOT_CONTAINS logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'msg', operator: 'NOT_CONTAINS', expectedValue: 'hello' });
    const res1 = evaluator.evaluateCondition(cond, { values: { msg: 'say goodbye' } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { msg: 'hello context' } });
    expect(res2.matched).toBe(false);
  });

  it('9. STARTS_WITH operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'STARTS_WITH', expectedValue: 'err_' });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 'err_connection_failed' } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 'success_ok' } });
    expect(res2.matched).toBe(false);
  });

  it('10. ENDS_WITH operator logic', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'ENDS_WITH', expectedValue: '_db' });
    const res1 = evaluator.evaluateCondition(cond, { values: { val: 'prod_cluster_db' } });
    expect(res1.matched).toBe(true);

    const res2 = evaluator.evaluateCondition(cond, { values: { val: 'prod_cluster' } });
    expect(res2.matched).toBe(false);
  });

  it('11. EXISTS / NOT_EXISTS logic', () => {
    const condExists = createRuleCondition({ id: 'c1', field: 'system.cpu', operator: 'EXISTS' });
    
    expect(evaluator.evaluateCondition(condExists, { values: { system: { cpu: 80 } } }).matched).toBe(true);
    expect(evaluator.evaluateCondition(condExists, { values: { system: { mem: 80 } } }).matched).toBe(false);
    expect(evaluator.evaluateCondition(condExists, { values: { system: { cpu: null } } }).matched).toBe(false);
    expect(evaluator.evaluateCondition(condExists, { values: { system: { cpu: undefined } } }).matched).toBe(false);

    const condNotExists = createRuleCondition({ id: 'c2', field: 'system.cpu', operator: 'NOT_EXISTS' });
    expect(evaluator.evaluateCondition(condNotExists, { values: { system: { mem: 80 } } }).matched).toBe(true);
    expect(evaluator.evaluateCondition(condNotExists, { values: { system: { cpu: 80 } } }).matched).toBe(false);
  });

  it('12. MATCHES regex logic (valid and invalid)', () => {
    const condMatches = createRuleCondition({ id: 'c1', field: 'val', operator: 'MATCHES', expectedValue: '^[0-9]+$' });
    const res1 = evaluator.evaluateCondition(condMatches, { values: { val: '12345' } });
    expect(res1.matched).toBe(true);
    expect(res1.status).toBe('MATCHED');

    const res2 = evaluator.evaluateCondition(condMatches, { values: { val: '123a45' } });
    expect(res2.matched).toBe(false);
    expect(res2.status).toBe('NOT_MATCHED');

    // Invalid regex pattern
    const condInvalid = createRuleCondition({ id: 'c2', field: 'val', operator: 'MATCHES', expectedValue: '[' });
    const res3 = evaluator.evaluateCondition(condInvalid, { values: { val: 'abc' } });
    expect(res3.matched).toBe(false);
    expect(res3.status).toBe('ERROR');
    expect(res3.reason).toBeDefined();
  });

  it('13. Path resolution (nested path, missing path, null, undefined)', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'a.b.c', operator: 'EQ', expectedValue: 'val' });
    
    // Nested resolves
    expect(evaluator.evaluateCondition(cond, { values: { a: { b: { c: 'val' } } } }).matched).toBe(true);
    
    // Missing path
    const resMissing = evaluator.evaluateCondition(cond, { values: { a: {} } });
    expect(resMissing.matched).toBe(false);
    expect(resMissing.status).toBe('NOT_MATCHED');

    // Null intermediate value
    const resNull = evaluator.evaluateCondition(cond, { values: { a: { b: null } } });
    expect(resNull.matched).toBe(false);
    expect(resNull.status).toBe('NOT_MATCHED');
  });

  it('14. Invalid comparison types (ERROR status)', () => {
    const cond = createRuleCondition({ id: 'c1', field: 'val', operator: 'GT', expectedValue: 100 });
    const res = evaluator.evaluateCondition(cond, { values: { val: 'not a number' } });
    expect(res.matched).toBe(false);
    expect(res.status).toBe('ERROR');
    expect(res.reason).toContain('numeric types');
  });

  it('15. ALL condition group logic', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const c2 = createRuleCondition({ id: 'c2', field: 'mem', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'ALL', conditions: [c1, c2] });

    // Both match
    const res1 = evaluator.evaluateGroup(group, { values: { cpu: 90, mem: 90 } });
    expect(res1.matched).toBe(true);
    expect(res1.conditions).toHaveLength(2);
    expect(res1.conditions[0].matched).toBe(true);
    expect(res1.conditions[1].matched).toBe(true);

    // One matches, one does not
    const res2 = evaluator.evaluateGroup(group, { values: { cpu: 90, mem: 50 } });
    expect(res2.matched).toBe(false);
    expect(res2.conditions[0].matched).toBe(true);
    expect(res2.conditions[1].matched).toBe(false);
  });

  it('16. ANY condition group logic', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const c2 = createRuleCondition({ id: 'c2', field: 'mem', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'ANY', conditions: [c1, c2] });

    // One matches
    const res1 = evaluator.evaluateGroup(group, { values: { cpu: 90, mem: 50 } });
    expect(res1.matched).toBe(true);

    // None matches
    const res2 = evaluator.evaluateGroup(group, { values: { cpu: 50, mem: 50 } });
    expect(res2.matched).toBe(false);
  });

  it('17. NOT condition group logic (nested errors)', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'NOT', conditions: [c1] });

    // Normal inversion
    expect(evaluator.evaluateGroup(group, { values: { cpu: 90 } }).matched).toBe(false);
    expect(evaluator.evaluateGroup(group, { values: { cpu: 50 } }).matched).toBe(true);

    // Inversion of error must not match
    const cErr = createRuleCondition({ id: 'cErr', field: 'cpu', operator: 'GT', expectedValue: 'invalid' as any });
    const groupErr = createConditionGroup({ operator: 'NOT', conditions: [cErr] });
    const resErr = evaluator.evaluateGroup(groupErr, { values: { cpu: 90 } });
    expect(resErr.matched).toBe(false);
  });

  it('18. Nested groups recursive logic', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const c2 = createRuleCondition({ id: 'c2', field: 'mem', operator: 'GT', expectedValue: 80 });
    const c3 = createRuleCondition({ id: 'c3', field: 'disk', operator: 'GT', expectedValue: 90 });

    const anyGroup = createConditionGroup({ operator: 'ANY', conditions: [c1, c2] });
    const rootGroup = createConditionGroup({ operator: 'ALL', conditions: [anyGroup, c3] });

    const res = evaluator.evaluateGroup(rootGroup, { values: { cpu: 90, mem: 50, disk: 95 } });
    expect(res.matched).toBe(true);
    expect(res.conditions[0].matched).toBe(true); // the ANY group matched
    expect(res.conditions[1].matched).toBe(true); // the disk condition matched
  });

  it('19. Disabled rules skip evaluation', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'ALL', conditions: [c1] });

    const rule = createAlertRule({
      id: 'rule-disabled',
      name: 'Rule',
      description: 'Desc',
      enabled: false,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const res = evaluator.evaluateRule(rule, { values: { cpu: 95 } });
    expect(res.matched).toBe(false);
    expect(res.status).toBe('SKIPPED');
    expect(res.results.conditions).toHaveLength(0);
  });

  it('20. Enabled rules evaluation tree error handling', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 'invalid' as any });
    const group = createConditionGroup({ operator: 'ALL', conditions: [c1] });

    const rule = createAlertRule({
      id: 'rule-error',
      name: 'Rule',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const res = evaluator.evaluateRule(rule, { values: { cpu: 95 } });
    expect(res.matched).toBe(false);
    expect(res.status).toBe('ERROR');
  });

  it('21. Rule result immutability', () => {
    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'ALL', conditions: [c1] });
    const rule = createAlertRule({
      id: 'rule-imm',
      name: 'Rule',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const res = evaluator.evaluateRule(rule, { values: { cpu: 95 } });
    expect(Object.isFrozen(res)).toBe(true);
    expect(Object.isFrozen(res.results)).toBe(true);
    expect(() => {
      (res as any).matched = false;
    }).toThrow();
  });

  it('22. Provider & Runtime delegation & Statistics updates', async () => {
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    const c1 = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
    const group = createConditionGroup({ operator: 'ALL', conditions: [c1] });
    const rule = createAlertRule({
      id: 'rule-del',
      name: 'Rule',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR',
      conditions: group,
      sourceId: 'src-1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const res1 = runtime.evaluateRule(rule, { values: { cpu: 95 } });
    expect(res1.matched).toBe(true);

    const stats1 = runtime.getStatistics();
    expect(stats1.totalEvaluations).toBe(1);
    expect(stats1.matchedEvaluations).toBe(1);
    expect(stats1.unmatchedEvaluations).toBe(0);
    expect(stats1.totalEvaluationDuration).toBeGreaterThanOrEqual(0);
    expect(stats1.averageEvaluationDuration).toBeGreaterThanOrEqual(0);

    const res2 = runtime.evaluateRule(rule, { values: { cpu: 50 } });
    expect(res2.matched).toBe(false);

    const stats2 = runtime.getStatistics();
    expect(stats2.totalEvaluations).toBe(2);
    expect(stats2.matchedEvaluations).toBe(1);
    expect(stats2.unmatchedEvaluations).toBe(1);
  });
});
