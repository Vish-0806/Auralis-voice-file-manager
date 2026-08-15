import { RuleCondition } from '../models/rule-condition';
import {
  AlertEvaluationContext,
  ConditionEvaluationResult,
  GroupEvaluationResult,
  RuleEvaluationResult
} from '../models/evaluation';
import { AlertRule } from '../models/alert-rule';
import { ConditionGroup } from '../models/condition-group';
import {
  createConditionEvaluationResult,
  createGroupEvaluationResult,
  createRuleEvaluationResult
} from '../factories/alertingFactories';
import { AlertRuleValidationError } from '../errors/AlertingErrors';

export class AlertEvaluator {
  public evaluateCondition(condition: RuleCondition, context: AlertEvaluationContext): ConditionEvaluationResult {
    const startTime = performance.now();
    const { exists, value: actualValue } = this.resolvePath(context.values, condition.field);

    try {
      const matched = this.evaluateOperator(condition.operator, actualValue, condition.expectedValue, exists);
      const durationMs = performance.now() - startTime;

      return createConditionEvaluationResult({
        conditionId: condition.id,
        matched,
        status: matched ? 'MATCHED' : 'NOT_MATCHED',
        actualValue,
        expectedValue: condition.expectedValue,
        operator: condition.operator,
        field: condition.field,
        durationMs
      });
    } catch (err: any) {
      const durationMs = performance.now() - startTime;
      return createConditionEvaluationResult({
        conditionId: condition.id,
        matched: false,
        status: 'ERROR',
        actualValue,
        expectedValue: condition.expectedValue,
        operator: condition.operator,
        field: condition.field,
        reason: err.message,
        error: { name: err.name || 'Error', message: err.message, stack: err.stack },
        durationMs
      });
    }
  }

  public evaluateGroup(group: ConditionGroup, context: AlertEvaluationContext): GroupEvaluationResult {
    const startTime = performance.now();
    const childrenResults: (ConditionEvaluationResult | GroupEvaluationResult)[] = [];

    // Evaluate all children recursively to conserve full diagnostic tree details
    for (const child of group.conditions) {
      if ('operator' in child && ['ALL', 'ANY', 'NOT'].includes(child.operator)) {
        childrenResults.push(this.evaluateGroup(child as ConditionGroup, context));
      } else {
        childrenResults.push(this.evaluateCondition(child as RuleCondition, context));
      }
    }

    let matched = false;
    if (group.operator === 'ALL') {
      matched = childrenResults.length > 0 && childrenResults.every(r => r.matched);
    } else if (group.operator === 'ANY') {
      matched = childrenResults.some(r => r.matched);
    } else if (group.operator === 'NOT') {
      if (childrenResults.length === 0) {
        matched = true;
      } else {
        const child = childrenResults[0];
        const isError = 'status' in child && (child as any).status === 'ERROR';
        if (isError) {
          matched = false;
        } else {
          matched = !child.matched;
        }
      }
    }

    const durationMs = performance.now() - startTime;
    return createGroupEvaluationResult({
      operator: group.operator,
      matched,
      conditions: childrenResults,
      durationMs
    });
  }

  public evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult {
    const startTime = performance.now();
    const evaluatedAt = Date.now();

    if (!rule || !rule.id) {
      throw new AlertRuleValidationError('Invalid rule: rule ID is required');
    }

    // Check enabled state
    if (!rule.enabled) {
      const durationMs = performance.now() - startTime;
      return createRuleEvaluationResult({
        ruleId: rule.id,
        ruleVersion: rule.version,
        matched: false,
        status: 'SKIPPED',
        results: createGroupEvaluationResult({
          operator: 'ALL',
          matched: false,
          conditions: []
        }),
        evaluatedAt,
        durationMs,
        metadata: {}
      });
    }

    try {
      const groupResult = this.evaluateGroup(rule.conditions, context);
      const matched = groupResult.matched;
      const durationMs = performance.now() - startTime;

      const hasError = this.hasTreeEvaluationError(groupResult);

      return createRuleEvaluationResult({
        ruleId: rule.id,
        ruleVersion: rule.version,
        matched,
        status: hasError ? 'ERROR' : (matched ? 'MATCHED' : 'NOT_MATCHED'),
        results: groupResult,
        evaluatedAt,
        durationMs,
        metadata: {}
      });
    } catch (err: any) {
      const durationMs = performance.now() - startTime;
      return createRuleEvaluationResult({
        ruleId: rule.id,
        ruleVersion: rule.version,
        matched: false,
        status: 'ERROR',
        results: createGroupEvaluationResult({
          operator: rule.conditions.operator,
          matched: false,
          conditions: []
        }),
        evaluatedAt,
        durationMs,
        error: { name: err.name || 'Error', message: err.message, stack: err.stack },
        metadata: {}
      });
    }
  }

  private hasTreeEvaluationError(result: ConditionEvaluationResult | GroupEvaluationResult): boolean {
    if ('status' in result) {
      return result.status === 'ERROR';
    }
    if ('conditions' in result) {
      return result.conditions.some(c => this.hasTreeEvaluationError(c));
    }
    return false;
  }

  private resolvePath(obj: any, path: string): { exists: boolean; value: any } {
    if (!path || typeof path !== 'string') {
      return { exists: false, value: undefined };
    }
    const parts = path.split('.');
    let current = obj;
    for (const part of parts) {
      if (current === null || current === undefined || typeof current !== 'object') {
        return { exists: false, value: undefined };
      }
      if (!(part in current)) {
        return { exists: false, value: undefined };
      }
      current = current[part];
    }
    return { exists: true, value: current };
  }

  private evaluateOperator(operator: string, actual: any, expected: any, exists: boolean): boolean {
    switch (operator) {
      case 'EXISTS':
        return exists && actual !== undefined && actual !== null;
      case 'NOT_EXISTS':
        return !exists || actual === undefined || actual === null;
      default:
        if (!exists || actual === undefined || actual === null) {
          return false;
        }
    }

    switch (operator) {
      case 'EQ':
        return actual === expected;
      case 'NEQ':
        return actual !== expected;
      case 'GT':
        if (typeof actual !== 'number' || typeof expected !== 'number') {
          throw new Error(`Comparison requires numeric types (actual: ${typeof actual}, expected: ${typeof expected})`);
        }
        return actual > expected;
      case 'GTE':
        if (typeof actual !== 'number' || typeof expected !== 'number') {
          throw new Error(`Comparison requires numeric types (actual: ${typeof actual}, expected: ${typeof expected})`);
        }
        return actual >= expected;
      case 'LT':
        if (typeof actual !== 'number' || typeof expected !== 'number') {
          throw new Error(`Comparison requires numeric types (actual: ${typeof actual}, expected: ${typeof expected})`);
        }
        return actual < expected;
      case 'LTE':
        if (typeof actual !== 'number' || typeof expected !== 'number') {
          throw new Error(`Comparison requires numeric types (actual: ${typeof actual}, expected: ${typeof expected})`);
        }
        return actual <= expected;
      case 'CONTAINS':
        if (typeof actual === 'string') {
          if (typeof expected !== 'string') {
            throw new Error('CONTAINS expects string or array search values');
          }
          return actual.includes(expected);
        }
        if (Array.isArray(actual)) {
          return actual.includes(expected);
        }
        throw new Error(`CONTAINS operator not supported for type ${typeof actual}`);
      case 'NOT_CONTAINS':
        if (typeof actual === 'string') {
          if (typeof expected !== 'string') {
            throw new Error('NOT_CONTAINS expects string or array search values');
          }
          return !actual.includes(expected);
        }
        if (Array.isArray(actual)) {
          return !actual.includes(expected);
        }
        throw new Error(`NOT_CONTAINS operator not supported for type ${typeof actual}`);
      case 'STARTS_WITH':
        if (typeof actual !== 'string' || typeof expected !== 'string') {
          throw new Error('STARTS_WITH operator requires both actual and expected values to be strings');
        }
        return actual.startsWith(expected);
      case 'ENDS_WITH':
        if (typeof actual !== 'string' || typeof expected !== 'string') {
          throw new Error('ENDS_WITH operator requires both actual and expected values to be strings');
        }
        return actual.endsWith(expected);
      case 'MATCHES':
        if (typeof actual !== 'string' || typeof expected !== 'string') {
          throw new Error('MATCHES operator requires string actual and pattern values');
        }
        try {
          const regex = new RegExp(expected);
          return regex.test(actual);
        } catch (err: any) {
          throw new Error(`Invalid regex pattern: ${err.message}`);
        }
      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }
}
