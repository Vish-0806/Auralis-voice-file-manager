import { AlertRule } from '../models/alert-rule';
import { RuleEvaluationResult } from '../models/evaluation';
import { AlertRecord, AlertState } from '../models/alert';
import { AlertGenerationError } from '../errors/AlertingErrors';
import { createAlertFingerprint } from '../factories/fingerprint';
import { freezeDeepSafe } from '../../models/monitoring';

let alertIdCounter = 0;

function generateAlertId(): string {
  alertIdCounter++;
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  const rand = Math.random().toString(16).substring(2, 10) + Math.random().toString(16).substring(2, 10);
  return `alert-${Date.now()}-${alertIdCounter}-${rand}`;
}

function extractTriggerIdentity(groupResult: any): Record<string, unknown> {
  const triggers: Record<string, unknown> = {};
  
  function walk(res: any) {
    if ('conditionId' in res) {
      if (res.matched) {
        triggers[res.conditionId] = {
          field: res.field,
          operator: res.operator,
          actualValue: res.actualValue,
          expectedValue: res.expectedValue
        };
      }
    } else if ('conditions' in res) {
      for (const child of res.conditions) {
        walk(child);
      }
    }
  }

  walk(groupResult);
  return triggers;
}

export class AlertGenerator {
  public generate(rule: AlertRule, evaluation: RuleEvaluationResult): AlertRecord {
    if (!rule) {
      throw new AlertGenerationError('rule is required to generate an alert');
    }
    if (!evaluation) {
      throw new AlertGenerationError('evaluation is required to generate an alert');
    }
    if (evaluation.ruleId !== rule.id) {
      throw new AlertGenerationError(`rule/evaluation ID mismatch: rule ID is ${rule.id}, but evaluation belongs to rule ${evaluation.ruleId}`);
    }
    if (!evaluation.matched) {
      throw new AlertGenerationError(`Cannot generate alert from evaluation: rule status is ${evaluation.status}`);
    }
    if (!rule.enabled) {
      throw new AlertGenerationError('Cannot generate alert for a disabled rule');
    }

    const generatedAt = Date.now();
    const alertId = generateAlertId();
    const triggerIdentity = extractTriggerIdentity(evaluation.results);

    const fingerprint = createAlertFingerprint(
      rule.id,
      rule.version,
      rule.severity,
      rule.sourceId,
      triggerIdentity
    );

    const metadata = {
      ...(rule.metadata ? JSON.parse(JSON.stringify(rule.metadata)) : {}),
      ...(evaluation.metadata ? JSON.parse(JSON.stringify(evaluation.metadata)) : {})
    };

    const alertRecord: AlertRecord = {
      id: alertId,
      sourceId: rule.sourceId,
      severity: rule.severity,
      state: AlertState.ACTIVE,
      title: rule.name,
      message: rule.description,
      createdAt: evaluation.evaluatedAt,
      updatedAt: generatedAt,
      metadata,

      // Phase 18.7.4 fields
      ruleId: rule.id,
      ruleVersion: rule.version,
      fingerprint,
      status: 'GENERATED',
      triggeredAt: evaluation.evaluatedAt,
      generatedAt,
      tags: rule.tags ? [...rule.tags] : [],
      evaluationResult: evaluation
    };

    return freezeDeepSafe(alertRecord);
  }
}
