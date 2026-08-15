import { AlertValidationError, AlertRuleValidationError } from '../errors/AlertingErrors';
import { AlertSeverity, AlertSeverityValue } from '../models/severity';
import { AlertState, AlertStateValue, AlertRecord } from '../models/alert';
import { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import { AlertOperator, AlertOperatorValue, RuleCondition } from '../models/rule-condition';
import { ConditionGroup } from '../models/condition-group';
import { AlertRule } from '../models/alert-rule';
import {
  ConditionEvaluationResult,
  GroupEvaluationResult,
  RuleEvaluationResult,
  ConditionEvaluationStatus,
  RuleEvaluationStatus
} from '../models/evaluation';
import { freezeDeepSafe } from '../../models/monitoring';

export function createAlertRecord(input: {
  id: string;
  sourceId: string;
  severity: AlertSeverityValue;
  state: AlertStateValue;
  title: string;
  message: string;
  createdAt: number;
  updatedAt: number;
  metadata?: Record<string, unknown>;
}): AlertRecord {
  if (!input.id || typeof input.id !== 'string' || input.id.trim() === '') {
    throw new AlertValidationError('Alert ID must be a non-empty string');
  }
  if (!input.sourceId || typeof input.sourceId !== 'string' || input.sourceId.trim() === '') {
    throw new AlertValidationError('Alert sourceId must be a non-empty string');
  }
  if (!Object.values(AlertSeverity).includes(input.severity)) {
    throw new AlertValidationError(`Invalid alert severity: ${input.severity}`);
  }
  if (!Object.values(AlertState).includes(input.state)) {
    throw new AlertValidationError(`Invalid alert state: ${input.state}`);
  }
  if (!input.title || typeof input.title !== 'string' || input.title.trim() === '') {
    throw new AlertValidationError('Alert title must be a non-empty string');
  }
  if (!input.message || typeof input.message !== 'string' || input.message.trim() === '') {
    throw new AlertValidationError('Alert message must be a non-empty string');
  }
  if (typeof input.createdAt !== 'number' || isNaN(input.createdAt) || input.createdAt < 0) {
    throw new AlertValidationError('Alert createdAt must be a valid timestamp');
  }
  if (typeof input.updatedAt !== 'number' || isNaN(input.updatedAt) || input.updatedAt < 0) {
    throw new AlertValidationError('Alert updatedAt must be a valid timestamp');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const record: AlertRecord = {
    id: input.id,
    sourceId: input.sourceId,
    severity: input.severity,
    state: input.state,
    title: input.title,
    message: input.message,
    createdAt: input.createdAt,
    updatedAt: input.updatedAt,
    metadata
  };

  return freezeDeepSafe(record);
}

export function createRuleCondition(input: {
  id: string;
  field: string;
  operator: AlertOperatorValue;
  expectedValue?: unknown;
  metadata?: Record<string, unknown>;
}): RuleCondition {
  if (!input.id || typeof input.id !== 'string' || input.id.trim() === '') {
    throw new AlertRuleValidationError('Condition ID must be a non-empty string');
  }
  if (!input.field || typeof input.field !== 'string' || input.field.trim() === '') {
    throw new AlertRuleValidationError('Condition field must be a non-empty string');
  }
  if (!Object.values(AlertOperator).includes(input.operator)) {
    throw new AlertRuleValidationError(`Invalid condition operator: ${input.operator}`);
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const condition: RuleCondition = {
    id: input.id,
    field: input.field,
    operator: input.operator,
    expectedValue: input.expectedValue,
    metadata
  };

  return freezeDeepSafe(condition);
}

export function createConditionGroup(input: {
  operator: 'ALL' | 'ANY' | 'NOT';
  conditions: ReadonlyArray<RuleCondition | ConditionGroup>;
}): ConditionGroup {
  if (!['ALL', 'ANY', 'NOT'].includes(input.operator)) {
    throw new AlertRuleValidationError(`Invalid condition group operator: ${input.operator}`);
  }
  if (!Array.isArray(input.conditions) || input.conditions.length === 0) {
    throw new AlertRuleValidationError('Condition group must contain a non-empty array of conditions');
  }

  // Deep clone to prevent external mutation
  const conditions = input.conditions.map(c => {
    if ('operator' in c && ['ALL', 'ANY', 'NOT'].includes(c.operator)) {
      return createConditionGroup(c as ConditionGroup);
    } else {
      return createRuleCondition(c as RuleCondition);
    }
  });

  const group: ConditionGroup = {
    operator: input.operator,
    conditions
  };

  return freezeDeepSafe(group);
}

function validateConditionGroup(group: ConditionGroup, depth: number, seenConditionIds: Set<string>): void {
  if (depth > 10) {
    throw new AlertRuleValidationError('Exceeded maximum nesting depth for condition groups');
  }
  if (!group || typeof group !== 'object') {
    throw new AlertRuleValidationError('Condition group must be a valid object');
  }
  if (!['ALL', 'ANY', 'NOT'].includes(group.operator)) {
    throw new AlertRuleValidationError(`Invalid condition group operator: ${group.operator}`);
  }
  if (!Array.isArray(group.conditions) || group.conditions.length === 0) {
    throw new AlertRuleValidationError('Condition group must contain a non-empty array of conditions');
  }

  for (const c of group.conditions) {
    if ('operator' in c && ['ALL', 'ANY', 'NOT'].includes(c.operator)) {
      validateConditionGroup(c as ConditionGroup, depth + 1, seenConditionIds);
    } else {
      const cond = c as RuleCondition;
      if (!cond.id || typeof cond.id !== 'string' || cond.id.trim() === '') {
        throw new AlertRuleValidationError('Condition ID must be a non-empty string');
      }
      if (!cond.field || typeof cond.field !== 'string' || cond.field.trim() === '') {
        throw new AlertRuleValidationError('Condition field must be a non-empty string');
      }
      if (!Object.values(AlertOperator).includes(cond.operator)) {
        throw new AlertRuleValidationError(`Invalid condition operator: ${cond.operator}`);
      }
      if (seenConditionIds.has(cond.id)) {
        throw new AlertRuleValidationError(`Duplicate condition ID '${cond.id}' within the rule`);
      }
      seenConditionIds.add(cond.id);
    }
  }
}

export function createAlertRule(input: {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  severity: AlertSeverityValue;
  conditions: ConditionGroup;
  sourceId: string;
  tags?: ReadonlyArray<string>;
  createdAt: number;
  updatedAt: number;
  version?: number;
  metadata?: Record<string, unknown>;
}): AlertRule {
  if (!input.id || typeof input.id !== 'string' || input.id.trim() === '') {
    throw new AlertRuleValidationError('Rule ID must be a non-empty string');
  }
  if (!input.name || typeof input.name !== 'string' || input.name.trim() === '') {
    throw new AlertRuleValidationError('Rule name must be a non-empty string');
  }
  if (typeof input.description !== 'string') {
    throw new AlertRuleValidationError('Rule description must be a string');
  }
  if (typeof input.enabled !== 'boolean') {
    throw new AlertRuleValidationError('Rule enabled state must be a boolean');
  }
  if (!Object.values(AlertSeverity).includes(input.severity)) {
    throw new AlertRuleValidationError(`Invalid rule severity: ${input.severity}`);
  }
  if (!input.sourceId || typeof input.sourceId !== 'string' || input.sourceId.trim() === '') {
    throw new AlertRuleValidationError('Rule sourceId must be a non-empty string');
  }
  if (typeof input.createdAt !== 'number' || isNaN(input.createdAt) || input.createdAt < 0) {
    throw new AlertRuleValidationError('Rule createdAt must be a valid timestamp');
  }
  if (typeof input.updatedAt !== 'number' || isNaN(input.updatedAt) || input.updatedAt < 0) {
    throw new AlertRuleValidationError('Rule updatedAt must be a valid timestamp');
  }
  if (input.version !== undefined && (typeof input.version !== 'number' || isNaN(input.version) || input.version < 0)) {
    throw new AlertRuleValidationError('Rule version must be a non-negative number');
  }

  // Validate condition group and check for duplicates recursively
  const seenConditionIds = new Set<string>();
  validateConditionGroup(input.conditions, 0, seenConditionIds);

  const tags = Array.isArray(input.tags) ? input.tags.map(t => String(t)) : [];
  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  // Deep copy condition group structure using createConditionGroup to ensure it's validated, frozen and copied
  const conditions = createConditionGroup(input.conditions);

  const rule: AlertRule = {
    id: input.id,
    name: input.name,
    description: input.description,
    enabled: input.enabled,
    severity: input.severity,
    conditions,
    sourceId: input.sourceId,
    tags,
    createdAt: input.createdAt,
    updatedAt: input.updatedAt,
    version: input.version,
    metadata
  };

  return freezeDeepSafe(rule);
}

export function createAlertingStatistics(input: {
  registeredAlertCount: number;
  registeredRuleCount: number;
  enabledRuleCount: number;
  disabledRuleCount: number;
  totalEvaluations: number;
  matchedEvaluations: number;
  unmatchedEvaluations: number;
  errorEvaluations: number;
  skippedEvaluations: number;
  totalEvaluationDuration: number;
  averageEvaluationDuration: number;
}): AlertingStatistics {
  const stats: AlertingStatistics = {
    registeredAlertCount: input.registeredAlertCount,
    registeredRuleCount: input.registeredRuleCount,
    enabledRuleCount: input.enabledRuleCount,
    disabledRuleCount: input.disabledRuleCount,
    totalEvaluations: input.totalEvaluations,
    matchedEvaluations: input.matchedEvaluations,
    unmatchedEvaluations: input.unmatchedEvaluations,
    errorEvaluations: input.errorEvaluations,
    skippedEvaluations: input.skippedEvaluations,
    totalEvaluationDuration: input.totalEvaluationDuration,
    averageEvaluationDuration: input.averageEvaluationDuration
  };

  return freezeDeepSafe(stats);
}

export function createAlertingDiagnostics(input: {
  runtimeState: string;
  registeredAlertCount: number;
  registeredRuleCount: number;
  enabledRuleCount: number;
  disabledRuleCount: number;
  totalEvaluations: number;
  matchedEvaluations: number;
  unmatchedEvaluations: number;
  errorEvaluations: number;
  skippedEvaluations: number;
  totalEvaluationDuration: number;
  averageEvaluationDuration: number;
  generatedAt: number;
}): AlertingDiagnostics {
  const diag: AlertingDiagnostics = {
    runtimeState: input.runtimeState,
    registeredAlertCount: input.registeredAlertCount,
    registeredRuleCount: input.registeredRuleCount,
    enabledRuleCount: input.enabledRuleCount,
    disabledRuleCount: input.disabledRuleCount,
    totalEvaluations: input.totalEvaluations,
    matchedEvaluations: input.matchedEvaluations,
    unmatchedEvaluations: input.unmatchedEvaluations,
    errorEvaluations: input.errorEvaluations,
    skippedEvaluations: input.skippedEvaluations,
    totalEvaluationDuration: input.totalEvaluationDuration,
    averageEvaluationDuration: input.averageEvaluationDuration,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(diag);
}

export function createConditionEvaluationResult(input: {
  conditionId: string;
  matched: boolean;
  status: any;
  actualValue: unknown;
  expectedValue: unknown;
  operator: string;
  field: string;
  reason?: string;
  error?: { name: string; message: string; stack?: string };
  durationMs?: number;
}): ConditionEvaluationResult {
  if (!input.conditionId) {
    throw new AlertRuleValidationError('Condition ID is required in evaluation result');
  }
  if (!input.field) {
    throw new AlertRuleValidationError('Field is required in evaluation result');
  }
  if (!input.operator) {
    throw new AlertRuleValidationError('Operator is required in evaluation result');
  }
  if (!Object.values(ConditionEvaluationStatus).includes(input.status)) {
    throw new AlertRuleValidationError(`Invalid condition evaluation status: ${input.status}`);
  }

  const result: ConditionEvaluationResult = {
    conditionId: input.conditionId,
    matched: input.matched,
    status: input.status,
    actualValue: input.actualValue,
    expectedValue: input.expectedValue,
    operator: input.operator,
    field: input.field,
    reason: input.reason,
    error: input.error,
    durationMs: input.durationMs
  };

  return freezeDeepSafe(result);
}

export function createGroupEvaluationResult(input: {
  operator: 'ALL' | 'ANY' | 'NOT';
  matched: boolean;
  conditions: ReadonlyArray<ConditionEvaluationResult | GroupEvaluationResult>;
  reason?: string;
  durationMs?: number;
}): GroupEvaluationResult {
  if (!['ALL', 'ANY', 'NOT'].includes(input.operator)) {
    throw new AlertRuleValidationError(`Invalid group operator: ${input.operator}`);
  }
  if (!Array.isArray(input.conditions)) {
    throw new AlertRuleValidationError('Conditions array is required in group evaluation result');
  }

  const result: GroupEvaluationResult = {
    operator: input.operator,
    matched: input.matched,
    conditions: input.conditions,
    reason: input.reason,
    durationMs: input.durationMs
  };

  return freezeDeepSafe(result);
}

export function createRuleEvaluationResult(input: {
  ruleId: string;
  ruleVersion?: number;
  matched: boolean;
  status: any;
  results: GroupEvaluationResult;
  evaluatedAt: number;
  durationMs: number;
  error?: { name: string; message: string; stack?: string };
  metadata?: Record<string, unknown>;
}): RuleEvaluationResult {
  if (!input.ruleId) {
    throw new AlertRuleValidationError('Rule ID is required in rule evaluation result');
  }
  if (!Object.values(RuleEvaluationStatus).includes(input.status)) {
    throw new AlertRuleValidationError(`Invalid rule evaluation status: ${input.status}`);
  }
  if (typeof input.evaluatedAt !== 'number' || input.evaluatedAt < 0) {
    throw new AlertRuleValidationError('EvaluatedAt timestamp is required');
  }
  if (typeof input.durationMs !== 'number' || input.durationMs < 0) {
    throw new AlertRuleValidationError('DurationMs must be a non-negative number');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const result: RuleEvaluationResult = {
    ruleId: input.ruleId,
    ruleVersion: input.ruleVersion,
    matched: input.matched,
    status: input.status,
    results: input.results,
    evaluatedAt: input.evaluatedAt,
    durationMs: input.durationMs,
    error: input.error,
    metadata
  };

  return freezeDeepSafe(result);
}
