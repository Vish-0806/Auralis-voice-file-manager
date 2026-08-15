import { describe, it, expect } from 'vitest';
import {
  AlertGenerator,
  AlertingProvider,
  AlertingRuntime,
  createAlertRule,
  createRuleCondition,
  createConditionGroup,
  createConditionEvaluationResult,
  createGroupEvaluationResult,
  createRuleEvaluationResult,
  createAlertFingerprint,
  AlertGenerationError
} from '../../../src/observability';

describe('AlertGenerator & Fingerprinting Tests', () => {
  const generator = new AlertGenerator();

  const cond = createRuleCondition({ id: 'c1', field: 'cpu', operator: 'GT', expectedValue: 80 });
  const group = createConditionGroup({ operator: 'ALL', conditions: [cond] });

  const validRule = createAlertRule({
    id: 'rule-1',
    name: 'Rule 1',
    description: 'Desc 1',
    enabled: true,
    severity: 'ERROR',
    conditions: group,
    sourceId: 'src-1',
    tags: ['cpu', 'system'],
    createdAt: Date.now(),
    updatedAt: Date.now(),
    metadata: { keyRule: 'ruleVal' }
  });

  const condResult = createConditionEvaluationResult({
    conditionId: 'c1',
    matched: true,
    status: 'MATCHED',
    actualValue: 90,
    expectedValue: 80,
    operator: 'GT',
    field: 'cpu'
  });

  const groupResult = createGroupEvaluationResult({
    operator: 'ALL',
    matched: true,
    conditions: [condResult]
  });

  const matchedEvaluation = createRuleEvaluationResult({
    ruleId: 'rule-1',
    ruleVersion: undefined,
    matched: true,
    status: 'MATCHED',
    results: groupResult,
    evaluatedAt: Date.now() - 5000,
    durationMs: 2,
    metadata: { keyEval: 'evalVal' }
  });

  it('1. Generate alert from MATCHED evaluation', () => {
    const alert = generator.generate(validRule, matchedEvaluation);
    expect(alert.id).toBeDefined();
    expect(alert.ruleId).toBe('rule-1');
    expect(alert.severity).toBe('ERROR');
    expect(alert.state).toBe('ACTIVE');
    expect(alert.title).toBe('Rule 1');
    expect(alert.message).toBe('Desc 1');
    expect(alert.status).toBe('GENERATED');
    expect(alert.fingerprint).toBeDefined();
    expect(alert.tags).toContain('cpu');
    expect(alert.metadata.keyRule).toBe('ruleVal');
    expect(alert.metadata.keyEval).toBe('evalVal');
  });

  it('2. Reject non-MATCHED evaluations', () => {
    const notMatchedEval = { ...matchedEvaluation, matched: false, status: 'NOT_MATCHED' as const };
    expect(() => generator.generate(validRule, notMatchedEval)).toThrow(AlertGenerationError);

    const errorEval = { ...matchedEvaluation, matched: false, status: 'ERROR' as const };
    expect(() => generator.generate(validRule, errorEval)).toThrow(AlertGenerationError);

    const skippedEval = { ...matchedEvaluation, matched: false, status: 'SKIPPED' as const };
    expect(() => generator.generate(validRule, skippedEval)).toThrow(AlertGenerationError);
  });

  it('3. Reject disabled rule or ID mismatch', () => {
    const disabledRule = { ...validRule, enabled: false };
    expect(() => generator.generate(disabledRule, matchedEvaluation)).toThrow(AlertGenerationError);

    const wrongRule = { ...validRule, id: 'rule-wrong' };
    expect(() => generator.generate(wrongRule, matchedEvaluation)).toThrow(AlertGenerationError);
  });

  it('4. Fingerprint determinism and property independence', () => {
    const f1 = createAlertFingerprint('r1', 1, 'ERROR', 'src', { c1: 'v1' });
    const f2 = createAlertFingerprint('r1', 1, 'ERROR', 'src', { c1: 'v1' });
    expect(f1).toBe(f2); // same inputs -> same fingerprint

    const fDiffRule = createAlertFingerprint('r2', 1, 'ERROR', 'src', { c1: 'v1' });
    expect(f1).not.toBe(fDiffRule); // different ruleId -> different fingerprint

    const fDiffVersion = createAlertFingerprint('r1', 2, 'ERROR', 'src', { c1: 'v1' });
    expect(f1).not.toBe(fDiffVersion); // different version -> different fingerprint

    const fDiffSource = createAlertFingerprint('r1', 1, 'ERROR', 'src-diff', { c1: 'v1' });
    expect(f1).not.toBe(fDiffSource); // different source -> different fingerprint
  });

  it('5. Canonical ordering stability for fingerprinting', () => {
    const trigger1 = { a: 1, b: 2, c: [10, 20] };
    const trigger2 = { b: 2, c: [10, 20], a: 1 }; // reordered properties

    const f1 = createAlertFingerprint('r1', 1, 'ERROR', 'src', trigger1);
    const f2 = createAlertFingerprint('r1', 1, 'ERROR', 'src', trigger2);

    expect(f1).toBe(f2); // reordering properties -> same fingerprint
  });

  it('6. Alert ID uniqueness', () => {
    const a1 = generator.generate(validRule, matchedEvaluation);
    const a2 = generator.generate(validRule, matchedEvaluation);
    expect(a1.id).not.toBe(a2.id); // distinct IDs
    expect(a1.fingerprint).toBe(a2.fingerprint); // same fingerprint (same logical cause)
  });

  it('7. Immutability checks', () => {
    const alert = generator.generate(validRule, matchedEvaluation);
    expect(Object.isFrozen(alert)).toBe(true);
    expect(Object.isFrozen(alert.tags)).toBe(true);
    expect(Object.isFrozen(alert.metadata)).toBe(true);

    expect(() => {
      (alert as any).title = 'Mutated';
    }).toThrow();
  });

  it('8. Provider and Runtime delegation & Statistics tracking', async () => {
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    runtime.registerRule(validRule);
    const alert = runtime.generateAlert(validRule, matchedEvaluation);

    expect(alert.ruleId).toBe('rule-1');
    expect(runtime.listAlerts()).toHaveLength(1);
    expect(runtime.getAlert(alert.id)).toBeDefined();

    // Re-generating same matching alert is allowed (no deduplication in this phase)
    runtime.generateAlert(validRule, matchedEvaluation);
    expect(runtime.listAlerts()).toHaveLength(2);

    const stats = runtime.getStatistics();
    expect(stats.totalAlertGenerations).toBe(2);
    expect(stats.successfulAlertGenerations).toBe(2);
    expect(stats.rejectedAlertGenerations).toBe(0);
    expect(stats.totalGenerationDuration).toBeGreaterThanOrEqual(0);
    expect(stats.averageGenerationDuration).toBeGreaterThanOrEqual(0);
  });
});
