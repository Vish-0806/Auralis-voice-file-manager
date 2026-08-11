import { AlertValidationError } from '../errors/AlertingErrors';
import {
  AlertSeverity,
  AlertSeverityValue,
  AlertState,
  AlertStateValue,
  AlertRecord
} from '../models/alert';
import { AlertRule } from '../models/rule';
import { AlertOperator, AlertCondition, AlertConditionGroup } from '../models/condition';
import { AlertEvaluationResult, AlertConditionResult } from '../models/evaluation';
import { AlertStatistics } from '../models/statistics';

// Implement freezeDeepSafe locally to ensure provider-independent immutability
function freezeDeepSafe<T>(value: T): T {
  if (Object.isFrozen(value)) {
    return value;
  }

  if (Array.isArray(value)) {
    const arrayValue = value.map((item) => freezeDeepSafe(item));
    return Object.freeze(arrayValue) as T;
  }

  if (value instanceof Map) {
    const newMap = new Map();
    value.forEach((v, k) => {
      newMap.set(freezeDeepSafe(k), freezeDeepSafe(v));
    });
    return Object.freeze(newMap) as unknown as T;
  }

  if (value instanceof Set) {
    const newSet = new Set();
    value.forEach((v) => {
      newSet.add(freezeDeepSafe(v));
    });
    return Object.freeze(newSet) as unknown as T;
  }

  if (value && typeof value === 'object') {
    if (value instanceof Error || value instanceof RegExp || value instanceof Date) {
      return Object.freeze(value);
    }
    const objectValue = value as Record<string, unknown>;
    const copy: Record<string, unknown> = {};
    Object.keys(objectValue).forEach((key) => {
      copy[key] = freezeDeepSafe(objectValue[key]);
    });
    return Object.freeze(copy) as unknown as T;
  }

  return value;
}

export function createAlertCondition(input: {
  field: string;
  operator: string;
  expectedValue?: unknown;
  threshold?: number;
  metadata?: Record<string, unknown>;
}): AlertCondition {
  if (!input.field || typeof input.field !== 'string') {
    throw new AlertValidationError('Alert condition field must be a non-empty string');
  }
  if (!Object.values(AlertOperator).includes(input.operator as any)) {
    throw new AlertValidationError(`Invalid alert condition operator: ${input.operator}`);
  }
  if (input.threshold !== undefined && typeof input.threshold !== 'number') {
    throw new AlertValidationError('Alert condition threshold must be a number');
  }

  const cond: AlertCondition = {
    field: input.field,
    operator: input.operator as any,
    expectedValue: input.expectedValue,
    threshold: input.threshold,
    metadata: input.metadata ? { ...input.metadata } : {}
  };

  return freezeDeepSafe(cond);
}

export function createAlertRule(input: {
  id: string;
  name: string;
  description: string;
  enabled?: boolean;
  severity: AlertSeverityValue;
  sourceId: string;
  priority?: number;
  cooldownMs?: number;
  suppressionMs?: number;
  expirationMs?: number;
  conditions: AlertConditionGroup | ReadonlyArray<AlertCondition>;
  metadata?: Record<string, unknown>;
}): AlertRule {
  if (!input.id || typeof input.id !== 'string') {
    throw new AlertValidationError('Alert rule id must be a non-empty string');
  }
  if (!input.name || typeof input.name !== 'string') {
    throw new AlertValidationError('Alert rule name must be a non-empty string');
  }
  if (!input.description || typeof input.description !== 'string') {
    throw new AlertValidationError('Alert rule description must be a non-empty string');
  }
  if (!Object.values(AlertSeverity).includes(input.severity)) {
    throw new AlertValidationError(`Invalid alert rule severity: ${input.severity}`);
  }
  if (!input.sourceId || typeof input.sourceId !== 'string') {
    throw new AlertValidationError('Alert rule sourceId must be a non-empty string');
  }
  if (input.cooldownMs !== undefined && (typeof input.cooldownMs !== 'number' || input.cooldownMs < 0)) {
    throw new AlertValidationError('Alert rule cooldownMs must be a non-negative number');
  }
  if (input.suppressionMs !== undefined && (typeof input.suppressionMs !== 'number' || input.suppressionMs < 0)) {
    throw new AlertValidationError('Alert rule suppressionMs must be a non-negative number');
  }
  if (input.expirationMs !== undefined && (typeof input.expirationMs !== 'number' || input.expirationMs < 0)) {
    throw new AlertValidationError('Alert rule expirationMs must be a non-negative number');
  }

  // Validate conditions
  if (!input.conditions) {
    throw new AlertValidationError('Alert rule conditions must be provided');
  }

  const rule: AlertRule = {
    id: input.id,
    name: input.name,
    description: input.description,
    enabled: input.enabled !== false,
    severity: input.severity,
    sourceId: input.sourceId,
    priority: typeof input.priority === 'number' ? input.priority : 0,
    cooldownMs: input.cooldownMs,
    suppressionMs: input.suppressionMs,
    expirationMs: input.expirationMs,
    conditions: input.conditions,
    metadata: input.metadata ? { ...input.metadata } : {}
  };

  return freezeDeepSafe(rule);
}

export function createAlertRecord(input: {
  id: string;
  ruleId: string;
  sourceId: string;
  fingerprint: string;
  severity: AlertSeverityValue;
  state: AlertStateValue;
  title: string;
  message: string;
  createdAt: number;
  updatedAt: number;
  acknowledgedAt?: number | null;
  acknowledgedBy?: string | null;
  resolvedAt?: number | null;
  resolvedBy?: string | null;
  suppressedUntil?: number | null;
  expiresAt?: number | null;
  metadata?: Record<string, unknown>;
}): AlertRecord {
  if (!input.id || typeof input.id !== 'string') {
    throw new AlertValidationError('Alert record id must be a non-empty string');
  }
  if (!input.ruleId || typeof input.ruleId !== 'string') {
    throw new AlertValidationError('Alert record ruleId must be a non-empty string');
  }
  if (!input.sourceId || typeof input.sourceId !== 'string') {
    throw new AlertValidationError('Alert record sourceId must be a non-empty string');
  }
  if (!input.fingerprint || typeof input.fingerprint !== 'string') {
    throw new AlertValidationError('Alert record fingerprint must be a non-empty string');
  }
  if (!Object.values(AlertSeverity).includes(input.severity)) {
    throw new AlertValidationError(`Invalid alert record severity: ${input.severity}`);
  }
  if (!Object.values(AlertState).includes(input.state)) {
    throw new AlertValidationError(`Invalid alert record state: ${input.state}`);
  }
  if (typeof input.createdAt !== 'number' || input.createdAt < 0) {
    throw new AlertValidationError('Alert record createdAt must be a valid timestamp');
  }
  if (typeof input.updatedAt !== 'number' || input.updatedAt < 0) {
    throw new AlertValidationError('Alert record updatedAt must be a valid timestamp');
  }

  const alert: AlertRecord = {
    id: input.id,
    ruleId: input.ruleId,
    sourceId: input.sourceId,
    fingerprint: input.fingerprint,
    severity: input.severity,
    state: input.state,
    title: input.title || '',
    message: input.message || '',
    createdAt: input.createdAt,
    updatedAt: input.updatedAt,
    acknowledgedAt: input.acknowledgedAt || null,
    acknowledgedBy: input.acknowledgedBy || null,
    resolvedAt: input.resolvedAt || null,
    resolvedBy: input.resolvedBy || null,
    suppressedUntil: input.suppressedUntil || null,
    expiresAt: input.expiresAt || null,
    metadata: input.metadata ? { ...input.metadata } : {}
  };

  return freezeDeepSafe(alert);
}

export function createAlertEvaluationResult(input: {
  ruleId: string;
  matched: boolean;
  evaluatedAt: number;
  duration: number;
  conditionResults: ReadonlyArray<AlertConditionResult>;
  reason?: string | null;
  error?: {
    name: string;
    message: string;
    stack?: string;
  } | null;
  metadata?: Record<string, unknown>;
}): AlertEvaluationResult {
  if (!input.ruleId || typeof input.ruleId !== 'string') {
    throw new AlertValidationError('Alert evaluation result ruleId must be a non-empty string');
  }
  if (typeof input.evaluatedAt !== 'number' || input.evaluatedAt < 0) {
    throw new AlertValidationError('Alert evaluation result evaluatedAt must be a valid timestamp');
  }
  if (typeof input.duration !== 'number' || input.duration < 0) {
    throw new AlertValidationError('Alert evaluation result duration must be a non-negative number');
  }

  const evalResult: AlertEvaluationResult = {
    ruleId: input.ruleId,
    matched: input.matched,
    evaluatedAt: input.evaluatedAt,
    duration: input.duration,
    conditionResults: input.conditionResults,
    reason: input.reason || null,
    error: input.error ? { ...input.error } : null,
    metadata: input.metadata ? { ...input.metadata } : {}
  };

  return freezeDeepSafe(evalResult);
}

export function createAlertStatistics(input: {
  totalEvaluations: number;
  matchedRules: number;
  unmatchedRules: number;
  alertsCreated: number;
  alertsDeduplicated: number;
  alertsAcknowledged: number;
  alertsSuppressed: number;
  alertsResumed: number;
  alertsResolved: number;
  alertsExpired: number;
  evaluationFailures: number;
  totalEvaluationDuration: number;
  averageEvaluationDuration: number;
  activeAlertCount: number;
  registeredRuleCount: number;
}): AlertStatistics {
  const stats: AlertStatistics = {
    totalEvaluations: typeof input.totalEvaluations === 'number' ? input.totalEvaluations : 0,
    matchedRules: typeof input.matchedRules === 'number' ? input.matchedRules : 0,
    unmatchedRules: typeof input.unmatchedRules === 'number' ? input.unmatchedRules : 0,
    alertsCreated: typeof input.alertsCreated === 'number' ? input.alertsCreated : 0,
    alertsDeduplicated: typeof input.alertsDeduplicated === 'number' ? input.alertsDeduplicated : 0,
    alertsAcknowledged: typeof input.alertsAcknowledged === 'number' ? input.alertsAcknowledged : 0,
    alertsSuppressed: typeof input.alertsSuppressed === 'number' ? input.alertsSuppressed : 0,
    alertsResumed: typeof input.alertsResumed === 'number' ? input.alertsResumed : 0,
    alertsResolved: typeof input.alertsResolved === 'number' ? input.alertsResolved : 0,
    alertsExpired: typeof input.alertsExpired === 'number' ? input.alertsExpired : 0,
    evaluationFailures: typeof input.evaluationFailures === 'number' ? input.evaluationFailures : 0,
    totalEvaluationDuration: typeof input.totalEvaluationDuration === 'number' ? input.totalEvaluationDuration : 0,
    averageEvaluationDuration: typeof input.averageEvaluationDuration === 'number' ? input.averageEvaluationDuration : 0,
    activeAlertCount: typeof input.activeAlertCount === 'number' ? input.activeAlertCount : 0,
    registeredRuleCount: typeof input.registeredRuleCount === 'number' ? input.registeredRuleCount : 0
  };

  return freezeDeepSafe(stats);
}

export function createAlertDiagnostics(input: {
  runtimeState: string;
  ruleCount: number;
  enabledRuleCount: number;
  activeAlertCount: number;
  historySize: number;
  statistics: AlertStatistics;
  generatedAt: number;
}) {
  const diag = {
    runtimeState: input.runtimeState,
    ruleCount: input.ruleCount,
    enabledRuleCount: input.enabledRuleCount,
    activeAlertCount: input.activeAlertCount,
    historySize: input.historySize,
    statistics: input.statistics,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(diag);
}

export function generateFingerprint(ruleId: string, sourceId: string, context?: Record<string, unknown>): string {
  let base = `${ruleId}:${sourceId}`;
  if (context) {
    const keys = Object.keys(context).sort();
    const parts = keys.map((k) => {
      const v = context[k];
      if (v !== null && typeof v === 'object') {
        return `${k}=${JSON.stringify(v)}`;
      }
      return `${k}=${v}`;
    });
    if (parts.length > 0) {
      base += `:${parts.join(',')}`;
    }
  }
  return base;
}

