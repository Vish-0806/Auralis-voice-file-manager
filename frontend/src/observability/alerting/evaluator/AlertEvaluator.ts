import { AlertRule } from '../models/rule';
import { AlertCondition, AlertConditionGroup, AlertOperator } from '../models/condition';
import { AlertEvaluationResult, AlertConditionResult } from '../models/evaluation';
import { createAlertEvaluationResult } from '../factories/alertingFactories';
import { AlertEvaluationError } from '../errors/AlertingErrors';

export class AlertEvaluator {
  public evaluate(rule: AlertRule, context: Record<string, unknown>): AlertEvaluationResult {
    const startTime = Date.now();
    const evaluatedAt = startTime;

    try {
      const conditionResults: AlertConditionResult[] = [];
      const matched = this.evaluateConditions(rule.conditions, context, conditionResults);

      const endTime = Date.now();
      const duration = endTime - startTime;

      const reason = matched
        ? `Alert rule '${rule.id}' matched successfully.`
        : `Alert rule '${rule.id}' did not match.`;

      return createAlertEvaluationResult({
        ruleId: rule.id,
        matched,
        evaluatedAt,
        duration,
        conditionResults,
        reason,
        error: null,
        metadata: {}
      });
    } catch (err: any) {
      const endTime = Date.now();
      const duration = endTime - startTime;

      const errorObj = err instanceof Error ? err : new Error(String(err));
      const errorInfo = {
        name: errorObj.name || 'Error',
        message: errorObj.message || String(err),
        stack: errorObj.stack
      };

      return createAlertEvaluationResult({
        ruleId: rule.id,
        matched: false,
        evaluatedAt,
        duration,
        conditionResults: [],
        reason: `Evaluation failed: ${errorObj.message}`,
        error: errorInfo,
        metadata: {}
      });
    }
  }

  private evaluateConditions(
    conditions: AlertConditionGroup | ReadonlyArray<AlertCondition>,
    context: Record<string, unknown>,
    results: AlertConditionResult[]
  ): boolean {
    if (Array.isArray(conditions)) {
      if (conditions.length === 0) return false;
      let allMatched = true;
      for (const cond of conditions) {
        const match = this.evaluateSingleCondition(cond, context, results);
        if (!match) {
          allMatched = false;
        }
      }
      return allMatched;
    } else {
      const group = conditions as AlertConditionGroup;
      if (!group.conditions || group.conditions.length === 0) return false;

      if (group.operator === 'ALL') {
        let allMatched = true;
        for (const child of group.conditions) {
          const match = this.evaluateConditions(child as any, context, results);
          if (!match) {
            allMatched = false;
          }
        }
        return allMatched;
      } else if (group.operator === 'ANY') {
        let anyMatched = false;
        for (const child of group.conditions) {
          const match = this.evaluateConditions(child as any, context, results);
          if (match) {
            anyMatched = true;
          }
        }
        return anyMatched;
      } else {
        throw new AlertEvaluationError(`Unknown condition group operator: ${group.operator}`);
      }
    }
  }

  private evaluateSingleCondition(
    condition: AlertCondition,
    context: Record<string, unknown>,
    results: AlertConditionResult[]
  ): boolean {
    const actualValue = this.getNestedValue(context, condition.field);
    let matched = false;

    switch (condition.operator) {
      case AlertOperator.EQUALS:
        matched = actualValue === condition.expectedValue;
        break;
      case AlertOperator.NOT_EQUALS:
        matched = actualValue !== condition.expectedValue;
        break;
      case AlertOperator.GREATER_THAN:
        matched = typeof actualValue === 'number' && actualValue > (condition.threshold ?? 0);
        break;
      case AlertOperator.GREATER_THAN_OR_EQUAL:
        matched = typeof actualValue === 'number' && actualValue >= (condition.threshold ?? 0);
        break;
      case AlertOperator.LESS_THAN:
        matched = typeof actualValue === 'number' && actualValue < (condition.threshold ?? 0);
        break;
      case AlertOperator.LESS_THAN_OR_EQUAL:
        matched = typeof actualValue === 'number' && actualValue <= (condition.threshold ?? 0);
        break;
      case AlertOperator.EXISTS:
        matched = actualValue !== undefined && actualValue !== null;
        break;
      case AlertOperator.NOT_EXISTS:
        matched = actualValue === undefined || actualValue === null;
        break;
      default:
        throw new AlertEvaluationError(`Invalid operator: ${condition.operator}`);
    }

    results.push({
      field: condition.field,
      matched,
      actualValue: actualValue === undefined ? null : actualValue,
      expectedValue: condition.expectedValue !== undefined ? condition.expectedValue : condition.threshold,
      operator: condition.operator
    });

    return matched;
  }

  private getNestedValue(obj: any, path: string): any {
    if (!obj || !path) return undefined;
    const parts = path.split('.');
    let current = obj;
    for (const part of parts) {
      if (current === null || typeof current !== 'object') {
        return undefined;
      }
      current = current[part];
    }
    return current;
  }
}
