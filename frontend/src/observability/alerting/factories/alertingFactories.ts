import { AlertValidationError, AlertRuleValidationError } from '../errors/AlertingErrors';
import { AlertSeverity, AlertSeverityValue } from '../models/severity';
import { AlertState, AlertStateValue, AlertRecord } from '../models/alert';
import { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import { AlertOperator, AlertOperatorValue, RuleCondition } from '../models/rule-condition';
import { ConditionGroup } from '../models/condition-group';
import { AlertRule } from '../models/alert-rule';
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
}): AlertingStatistics {
  if (typeof input.registeredAlertCount !== 'number' || isNaN(input.registeredAlertCount) || input.registeredAlertCount < 0) {
    throw new AlertValidationError('registeredAlertCount must be a non-negative number');
  }
  if (typeof input.registeredRuleCount !== 'number' || isNaN(input.registeredRuleCount) || input.registeredRuleCount < 0) {
    throw new AlertValidationError('registeredRuleCount must be a non-negative number');
  }
  if (typeof input.enabledRuleCount !== 'number' || isNaN(input.enabledRuleCount) || input.enabledRuleCount < 0) {
    throw new AlertValidationError('enabledRuleCount must be a non-negative number');
  }
  if (typeof input.disabledRuleCount !== 'number' || isNaN(input.disabledRuleCount) || input.disabledRuleCount < 0) {
    throw new AlertValidationError('disabledRuleCount must be a non-negative number');
  }

  const stats: AlertingStatistics = {
    registeredAlertCount: input.registeredAlertCount,
    registeredRuleCount: input.registeredRuleCount,
    enabledRuleCount: input.enabledRuleCount,
    disabledRuleCount: input.disabledRuleCount
  };

  return freezeDeepSafe(stats);
}

export function createAlertingDiagnostics(input: {
  runtimeState: string;
  registeredAlertCount: number;
  registeredRuleCount: number;
  enabledRuleCount: number;
  disabledRuleCount: number;
  generatedAt: number;
}): AlertingDiagnostics {
  if (typeof input.runtimeState !== 'string' || input.runtimeState.trim() === '') {
    throw new AlertValidationError('runtimeState must be a non-empty string');
  }
  if (typeof input.registeredAlertCount !== 'number' || isNaN(input.registeredAlertCount) || input.registeredAlertCount < 0) {
    throw new AlertValidationError('registeredAlertCount must be a non-negative number');
  }
  if (typeof input.registeredRuleCount !== 'number' || isNaN(input.registeredRuleCount) || input.registeredRuleCount < 0) {
    throw new AlertValidationError('registeredRuleCount must be a non-negative number');
  }
  if (typeof input.enabledRuleCount !== 'number' || isNaN(input.enabledRuleCount) || input.enabledRuleCount < 0) {
    throw new AlertValidationError('enabledRuleCount must be a non-negative number');
  }
  if (typeof input.disabledRuleCount !== 'number' || isNaN(input.disabledRuleCount) || input.disabledRuleCount < 0) {
    throw new AlertValidationError('disabledRuleCount must be a non-negative number');
  }
  if (typeof input.generatedAt !== 'number' || isNaN(input.generatedAt) || input.generatedAt < 0) {
    throw new AlertValidationError('generatedAt must be a valid timestamp');
  }

  const diag: AlertingDiagnostics = {
    runtimeState: input.runtimeState,
    registeredAlertCount: input.registeredAlertCount,
    registeredRuleCount: input.registeredRuleCount,
    enabledRuleCount: input.enabledRuleCount,
    disabledRuleCount: input.disabledRuleCount,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(diag);
}
