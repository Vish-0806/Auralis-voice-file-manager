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
import {
  DeduplicationDecision,
  DeduplicationRecord,
  DeduplicationDecisionType
} from '../models/deduplication';
import {
  AlertLifecycleState,
  AlertLifecycleStateValue,
  AlertLifecycleActor,
  AlertLifecycleActorValue,
  AlertLifecycleHistoryEntry,
  AlertLifecycleRecord
} from '../models/lifecycle';
import {
  AlertSuppressionReason,
  AlertSuppressionReasonValue,
  AlertSuppressionScope,
  AlertSuppressionScopeValue,
  AlertSuppressionPolicy,
  AlertMaintenanceWindow,
  AlertSnoozeRecord,
  AlertSuppressionDecision
} from '../models/suppression';
import {
  NotificationChannelType,
  NotificationChannelTypeValue,
  NotificationPriority,
  NotificationPriorityValue,
  NotificationDeliveryStatus,
  NotificationDeliveryStatusValue,
  NotificationRecipient,
  NotificationPayload,
  NotificationRequest,
  NotificationDeliveryAttempt,
  NotificationDeliveryResult
} from '../models/notification';
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
  totalAlertGenerations: number;
  successfulAlertGenerations: number;
  rejectedAlertGenerations: number;
  generationErrors: number;
  totalGenerationDuration: number;
  averageGenerationDuration: number;
  totalDeduplicationChecks: number;
  acceptedAlertCount: number;
  duplicateAlertCount: number;
  cooldownSuppressedCount: number;
  activeCooldownCount: number;
  trackedFingerprintCount: number;
  lifecycleTransitions: number;
  acknowledgements: number;
  resolutions: number;
  closures: number;
  invalidTransitions: number;
  activeAlerts: number;
  acknowledgedAlerts: number;
  resolvedAlerts: number;
  closedAlerts: number;
  suppressionEvaluations: number;
  suppressedAlerts: number;
  allowedAlerts: number;
  policyMatches: number;
  maintenanceMatches: number;
  snoozedMatches: number;
  evaluationFailures: number;
  activePolicies: number;
  activeMaintenanceWindows: number;
  activeSnoozes: number;
  notificationRequests: number;
  validationFailures: number;
  dispatchedNotifications: number;
  deliveredNotifications: number;
  failedNotifications: number;
  skippedNotifications: number;
  cancelledNotifications: number;
  retryAttempts: number;
  registeredChannels: number;
  enabledChannels: number;
  disabledChannels: number;
  averageDeliveryDuration: number;
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
    averageEvaluationDuration: input.averageEvaluationDuration,
    totalAlertGenerations: input.totalAlertGenerations,
    successfulAlertGenerations: input.successfulAlertGenerations,
    rejectedAlertGenerations: input.rejectedAlertGenerations,
    generationErrors: input.generationErrors,
    totalGenerationDuration: input.totalGenerationDuration,
    averageGenerationDuration: input.averageGenerationDuration,
    totalDeduplicationChecks: input.totalDeduplicationChecks,
    acceptedAlertCount: input.acceptedAlertCount,
    duplicateAlertCount: input.duplicateAlertCount,
    cooldownSuppressedCount: input.cooldownSuppressedCount,
    activeCooldownCount: input.activeCooldownCount,
    trackedFingerprintCount: input.trackedFingerprintCount,
    lifecycleTransitions: input.lifecycleTransitions,
    acknowledgements: input.acknowledgements,
    resolutions: input.resolutions,
    closures: input.closures,
    invalidTransitions: input.invalidTransitions,
    activeAlerts: input.activeAlerts,
    acknowledgedAlerts: input.acknowledgedAlerts,
    resolvedAlerts: input.resolvedAlerts,
    closedAlerts: input.closedAlerts,
    suppressionEvaluations: input.suppressionEvaluations,
    suppressedAlerts: input.suppressedAlerts,
    allowedAlerts: input.allowedAlerts,
    policyMatches: input.policyMatches,
    maintenanceMatches: input.maintenanceMatches,
    snoozedMatches: input.snoozedMatches,
    evaluationFailures: input.evaluationFailures,
    activePolicies: input.activePolicies,
    activeMaintenanceWindows: input.activeMaintenanceWindows,
    activeSnoozes: input.activeSnoozes,
    notificationRequests: input.notificationRequests,
    validationFailures: input.validationFailures,
    dispatchedNotifications: input.dispatchedNotifications,
    deliveredNotifications: input.deliveredNotifications,
    failedNotifications: input.failedNotifications,
    skippedNotifications: input.skippedNotifications,
    cancelledNotifications: input.cancelledNotifications,
    retryAttempts: input.retryAttempts,
    registeredChannels: input.registeredChannels,
    enabledChannels: input.enabledChannels,
    disabledChannels: input.disabledChannels,
    averageDeliveryDuration: input.averageDeliveryDuration
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
  totalAlertGenerations: number;
  successfulAlertGenerations: number;
  rejectedAlertGenerations: number;
  generationErrors: number;
  totalGenerationDuration: number;
  averageGenerationDuration: number;
  totalDeduplicationChecks: number;
  acceptedAlertCount: number;
  duplicateAlertCount: number;
  cooldownSuppressedCount: number;
  activeCooldownCount: number;
  trackedFingerprintCount: number;
  lifecycleTransitions: number;
  acknowledgements: number;
  resolutions: number;
  closures: number;
  invalidTransitions: number;
  activeAlerts: number;
  acknowledgedAlerts: number;
  resolvedAlerts: number;
  closedAlerts: number;
  suppressionEvaluations: number;
  suppressedAlerts: number;
  allowedAlerts: number;
  policyMatches: number;
  maintenanceMatches: number;
  snoozedMatches: number;
  evaluationFailures: number;
  activePolicies: number;
  activeMaintenanceWindows: number;
  activeSnoozes: number;
  notificationRequests: number;
  validationFailures: number;
  dispatchedNotifications: number;
  deliveredNotifications: number;
  failedNotifications: number;
  skippedNotifications: number;
  cancelledNotifications: number;
  retryAttempts: number;
  registeredChannels: number;
  enabledChannels: number;
  disabledChannels: number;
  averageDeliveryDuration: number;
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
    totalAlertGenerations: input.totalAlertGenerations,
    successfulAlertGenerations: input.successfulAlertGenerations,
    rejectedAlertGenerations: input.rejectedAlertGenerations,
    generationErrors: input.generationErrors,
    totalGenerationDuration: input.totalGenerationDuration,
    averageGenerationDuration: input.averageGenerationDuration,
    totalDeduplicationChecks: input.totalDeduplicationChecks,
    acceptedAlertCount: input.acceptedAlertCount,
    duplicateAlertCount: input.duplicateAlertCount,
    cooldownSuppressedCount: input.cooldownSuppressedCount,
    activeCooldownCount: input.activeCooldownCount,
    trackedFingerprintCount: input.trackedFingerprintCount,
    lifecycleTransitions: input.lifecycleTransitions,
    acknowledgements: input.acknowledgements,
    resolutions: input.resolutions,
    closures: input.closures,
    invalidTransitions: input.invalidTransitions,
    activeAlerts: input.activeAlerts,
    acknowledgedAlerts: input.acknowledgedAlerts,
    resolvedAlerts: input.resolvedAlerts,
    closedAlerts: input.closedAlerts,
    suppressionEvaluations: input.suppressionEvaluations,
    suppressedAlerts: input.suppressedAlerts,
    allowedAlerts: input.allowedAlerts,
    policyMatches: input.policyMatches,
    maintenanceMatches: input.maintenanceMatches,
    snoozedMatches: input.snoozedMatches,
    evaluationFailures: input.evaluationFailures,
    activePolicies: input.activePolicies,
    activeMaintenanceWindows: input.activeMaintenanceWindows,
    activeSnoozes: input.activeSnoozes,
    notificationRequests: input.notificationRequests,
    validationFailures: input.validationFailures,
    dispatchedNotifications: input.dispatchedNotifications,
    deliveredNotifications: input.deliveredNotifications,
    failedNotifications: input.failedNotifications,
    skippedNotifications: input.skippedNotifications,
    cancelledNotifications: input.cancelledNotifications,
    retryAttempts: input.retryAttempts,
    registeredChannels: input.registeredChannels,
    enabledChannels: input.enabledChannels,
    disabledChannels: input.disabledChannels,
    averageDeliveryDuration: input.averageDeliveryDuration,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(diag);
}

export function createDeduplicationDecision(input: {
  fingerprint: string;
  alertId: string;
  decision: any;
  duplicate: boolean;
  cooldownSuppressed: boolean;
  firstSeenAt: number;
  lastSeenAt: number;
  nextEligibleAt: number;
  occurrenceCount: number;
  evaluatedAt: number;
  reason: string;
}): DeduplicationDecision {
  if (!input.fingerprint) {
    throw new AlertRuleValidationError('fingerprint is required in deduplication decision');
  }
  if (!input.alertId) {
    throw new AlertRuleValidationError('alertId is required in deduplication decision');
  }
  if (!Object.values(DeduplicationDecisionType).includes(input.decision)) {
    throw new AlertRuleValidationError(`Invalid deduplication decision: ${input.decision}`);
  }

  const result: DeduplicationDecision = {
    fingerprint: input.fingerprint,
    alertId: input.alertId,
    decision: input.decision,
    duplicate: input.duplicate,
    cooldownSuppressed: input.cooldownSuppressed,
    firstSeenAt: input.firstSeenAt,
    lastSeenAt: input.lastSeenAt,
    nextEligibleAt: input.nextEligibleAt,
    occurrenceCount: input.occurrenceCount,
    evaluatedAt: input.evaluatedAt,
    reason: input.reason
  };

  return freezeDeepSafe(result);
}

export function createDeduplicationRecord(input: {
  fingerprint: string;
  firstSeenAt: number;
  lastSeenAt: number;
  occurrenceCount: number;
  acceptedCount: number;
  duplicateCount: number;
  cooldownSuppressionCount: number;
  nextEligibleAt: number;
  ruleId?: string;
  sourceId?: string;
}): DeduplicationRecord {
  if (!input.fingerprint) {
    throw new AlertRuleValidationError('fingerprint is required in deduplication record');
  }

  const result: DeduplicationRecord = {
    fingerprint: input.fingerprint,
    firstSeenAt: input.firstSeenAt,
    lastSeenAt: input.lastSeenAt,
    occurrenceCount: input.occurrenceCount,
    acceptedCount: input.acceptedCount,
    duplicateCount: input.duplicateCount,
    cooldownSuppressionCount: input.cooldownSuppressionCount,
    nextEligibleAt: input.nextEligibleAt,
    ruleId: input.ruleId,
    sourceId: input.sourceId
  };

  return freezeDeepSafe(result);
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

export function createAlertLifecycleHistoryEntry(input: {
  alertId: string;
  fingerprint?: string;
  previousState: AlertLifecycleStateValue | null;
  nextState: AlertLifecycleStateValue;
  timestamp: number;
  actor: AlertLifecycleActorValue;
  operation: string;
  reason?: string;
  metadata?: Record<string, unknown>;
}): AlertLifecycleHistoryEntry {
  if (!input.alertId) {
    throw new AlertRuleValidationError('alertId is required in lifecycle history entry');
  }
  if (!Object.values(AlertLifecycleState).includes(input.nextState)) {
    throw new AlertRuleValidationError(`Invalid lifecycle nextState: ${input.nextState}`);
  }
  if (input.previousState !== null && !Object.values(AlertLifecycleState).includes(input.previousState)) {
    throw new AlertRuleValidationError(`Invalid lifecycle previousState: ${input.previousState}`);
  }
  if (!Object.values(AlertLifecycleActor).includes(input.actor)) {
    throw new AlertRuleValidationError(`Invalid lifecycle actor: ${input.actor}`);
  }
  if (!input.operation) {
    throw new AlertRuleValidationError('operation is required in lifecycle history entry');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const entry: AlertLifecycleHistoryEntry = {
    alertId: input.alertId,
    fingerprint: input.fingerprint,
    previousState: input.previousState,
    nextState: input.nextState,
    timestamp: input.timestamp,
    actor: input.actor,
    operation: input.operation,
    reason: input.reason,
    metadata
  };

  return freezeDeepSafe(entry);
}

export function createAlertLifecycleRecord(input: {
  alertId: string;
  fingerprint?: string;
  state: AlertLifecycleStateValue;
  createdAt: number;
  updatedAt: number;
  history: ReadonlyArray<AlertLifecycleHistoryEntry>;
  metadata?: Record<string, unknown>;
}): AlertLifecycleRecord {
  if (!input.alertId) {
    throw new AlertRuleValidationError('alertId is required in lifecycle record');
  }
  if (!Object.values(AlertLifecycleState).includes(input.state)) {
    throw new AlertRuleValidationError(`Invalid lifecycle state: ${input.state}`);
  }
  if (!Array.isArray(input.history)) {
    throw new AlertRuleValidationError('history array is required in lifecycle record');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const record: AlertLifecycleRecord = {
    alertId: input.alertId,
    fingerprint: input.fingerprint,
    state: input.state,
    createdAt: input.createdAt,
    updatedAt: input.updatedAt,
    history: input.history,
    metadata
  };

  return freezeDeepSafe(record);
}

export function createAlertSuppressionPolicy(input: {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;
  scope: AlertSuppressionScopeValue;
  ruleId?: string;
  alertId?: string;
  fingerprint?: string;
  sourceId?: string;
  startTime?: number;
  endTime?: number;
  reason: AlertSuppressionReasonValue;
  metadata?: Record<string, unknown>;
}): AlertSuppressionPolicy {
  if (!input.id) {
    throw new AlertRuleValidationError('Policy ID is required');
  }
  if (!input.name) {
    throw new AlertRuleValidationError('Policy name is required');
  }
  if (typeof input.priority !== 'number' || isNaN(input.priority)) {
    throw new AlertRuleValidationError('Policy priority must be a valid number');
  }
  if (!Object.values(AlertSuppressionScope).includes(input.scope)) {
    throw new AlertRuleValidationError(`Invalid policy scope: ${input.scope}`);
  }
  if (!Object.values(AlertSuppressionReason).includes(input.reason)) {
    throw new AlertRuleValidationError(`Invalid policy reason: ${input.reason}`);
  }
  if (input.startTime !== undefined && (typeof input.startTime !== 'number' || input.startTime < 0)) {
    throw new AlertRuleValidationError('Invalid policy startTime');
  }
  if (input.endTime !== undefined && (typeof input.endTime !== 'number' || input.endTime < 0)) {
    throw new AlertRuleValidationError('Invalid policy endTime');
  }
  if (input.startTime !== undefined && input.endTime !== undefined && input.startTime >= input.endTime) {
    throw new AlertRuleValidationError('Policy startTime must be less than endTime');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const policy: AlertSuppressionPolicy = {
    id: input.id,
    name: input.name,
    enabled: input.enabled,
    priority: input.priority,
    scope: input.scope,
    ruleId: input.ruleId,
    alertId: input.alertId,
    fingerprint: input.fingerprint,
    sourceId: input.sourceId,
    startTime: input.startTime,
    endTime: input.endTime,
    reason: input.reason,
    metadata
  };

  return freezeDeepSafe(policy);
}

export function createAlertMaintenanceWindow(input: {
  id: string;
  name: string;
  enabled: boolean;
  startTime: number;
  endTime: number;
  scope?: AlertSuppressionScopeValue;
  reason: string;
  metadata?: Record<string, unknown>;
}): AlertMaintenanceWindow {
  if (!input.id) {
    throw new AlertRuleValidationError('Maintenance Window ID is required');
  }
  if (!input.name) {
    throw new AlertRuleValidationError('Maintenance Window name is required');
  }
  if (typeof input.startTime !== 'number' || isNaN(input.startTime) || input.startTime < 0) {
    throw new AlertRuleValidationError('Invalid maintenance window startTime');
  }
  if (typeof input.endTime !== 'number' || isNaN(input.endTime) || input.endTime < 0) {
    throw new AlertRuleValidationError('Invalid maintenance window endTime');
  }
  if (input.startTime >= input.endTime) {
    throw new AlertRuleValidationError('Maintenance window startTime must be less than endTime');
  }
  if (input.scope !== undefined && !Object.values(AlertSuppressionScope).includes(input.scope)) {
    throw new AlertRuleValidationError(`Invalid maintenance window scope: ${input.scope}`);
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const window: AlertMaintenanceWindow = {
    id: input.id,
    name: input.name,
    enabled: input.enabled,
    startTime: input.startTime,
    endTime: input.endTime,
    scope: input.scope,
    reason: input.reason,
    metadata
  };

  return freezeDeepSafe(window);
}

export function createAlertSnoozeRecord(input: {
  alertId: string;
  fingerprint?: string;
  startTime: number;
  endTime: number;
  actor: string;
  reason?: string;
  metadata?: Record<string, unknown>;
}): AlertSnoozeRecord {
  if (!input.alertId) {
    throw new AlertRuleValidationError('Snooze Alert ID is required');
  }
  if (typeof input.startTime !== 'number' || isNaN(input.startTime) || input.startTime < 0) {
    throw new AlertRuleValidationError('Invalid snooze startTime');
  }
  if (typeof input.endTime !== 'number' || isNaN(input.endTime) || input.endTime < 0) {
    throw new AlertRuleValidationError('Invalid snooze endTime');
  }
  if (input.startTime >= input.endTime) {
    throw new AlertRuleValidationError('Snooze startTime must be less than endTime');
  }
  if (!input.actor) {
    throw new AlertRuleValidationError('Snooze actor is required');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const snooze: AlertSnoozeRecord = {
    alertId: input.alertId,
    fingerprint: input.fingerprint,
    startTime: input.startTime,
    endTime: input.endTime,
    actor: input.actor,
    reason: input.reason,
    metadata
  };

  return freezeDeepSafe(snooze);
}

export function createAlertSuppressionDecision(input: {
  suppressed: boolean;
  reason: AlertSuppressionReasonValue | null;
  policyId?: string;
  windowId?: string;
  evaluatedAt: number;
  metadata?: Record<string, unknown>;
}): AlertSuppressionDecision {
  if (input.suppressed && !input.reason) {
    throw new AlertRuleValidationError('reason is required when alert is suppressed');
  }
  if (input.reason !== null && !Object.values(AlertSuppressionReason).includes(input.reason)) {
    throw new AlertRuleValidationError(`Invalid suppression reason: ${input.reason}`);
  }
  if (typeof input.evaluatedAt !== 'number' || isNaN(input.evaluatedAt) || input.evaluatedAt < 0) {
    throw new AlertRuleValidationError('Invalid suppression evaluatedAt timestamp');
  }

  const metadata = input.metadata ? JSON.parse(JSON.stringify(input.metadata)) : {};

  const decision: AlertSuppressionDecision = {
    suppressed: input.suppressed,
    reason: input.reason,
    policyId: input.policyId,
    windowId: input.windowId,
    evaluatedAt: input.evaluatedAt,
    metadata
  };

  return freezeDeepSafe(decision);
}

export function createNotificationRequest(input: {
  id: string;
  alertId: string;
  fingerprint?: string;
  channelId: string;
  payload: NotificationPayload;
  priority: NotificationPriorityValue;
  channelType: NotificationChannelTypeValue;
  recipient: NotificationRecipient;
  createdAt: number;
  correlationId?: string;
}): NotificationRequest {
  if (!input.id) {
    throw new AlertRuleValidationError('Notification ID is required');
  }
  if (!input.alertId) {
    throw new AlertRuleValidationError('Alert ID is required');
  }
  if (!input.channelId) {
    throw new AlertRuleValidationError('Channel ID is required');
  }
  if (!input.payload) {
    throw new AlertRuleValidationError('Payload is required');
  }
  if (!input.payload.title) {
    throw new AlertRuleValidationError('Payload title is required');
  }
  if (!input.payload.message) {
    throw new AlertRuleValidationError('Payload message is required');
  }
  if (!input.recipient) {
    throw new AlertRuleValidationError('Recipient info is required');
  }
  if (!input.recipient.id) {
    throw new AlertRuleValidationError('Recipient ID is required');
  }
  if (!input.recipient.name) {
    throw new AlertRuleValidationError('Recipient name is required');
  }
  if (typeof input.createdAt !== 'number' || isNaN(input.createdAt) || input.createdAt < 0) {
    throw new AlertRuleValidationError('Invalid notification createdAt timestamp');
  }
  if (!Object.values(NotificationPriority).includes(input.priority)) {
    throw new AlertRuleValidationError(`Invalid priority: ${input.priority}`);
  }
  if (!Object.values(NotificationChannelType).includes(input.channelType)) {
    throw new AlertRuleValidationError(`Invalid channelType: ${input.channelType}`);
  }

  const payload = freezeDeepSafe(input.payload);
  const recipient = freezeDeepSafe(input.recipient);

  const request: NotificationRequest = {
    id: input.id,
    alertId: input.alertId,
    fingerprint: input.fingerprint,
    channelId: input.channelId,
    payload,
    priority: input.priority,
    channelType: input.channelType,
    recipient,
    createdAt: input.createdAt,
    correlationId: input.correlationId
  };

  return freezeDeepSafe(request);
}

export function createNotificationDeliveryAttempt(input: {
  notificationId: string;
  attempt: number;
  status: NotificationDeliveryStatusValue;
  timestamp: number;
  duration: number;
  error?: { name: string; message: string; stack?: string };
}): NotificationDeliveryAttempt {
  if (!input.notificationId) {
    throw new AlertRuleValidationError('Notification ID is required for delivery attempt');
  }
  if (typeof input.attempt !== 'number' || isNaN(input.attempt) || input.attempt <= 0) {
    throw new AlertRuleValidationError('Invalid attempt number');
  }
  if (!Object.values(NotificationDeliveryStatus).includes(input.status)) {
    throw new AlertRuleValidationError(`Invalid delivery attempt status: ${input.status}`);
  }
  if (typeof input.timestamp !== 'number' || isNaN(input.timestamp) || input.timestamp < 0) {
    throw new AlertRuleValidationError('Invalid timestamp');
  }
  if (typeof input.duration !== 'number' || isNaN(input.duration) || input.duration < 0) {
    throw new AlertRuleValidationError('Invalid duration');
  }

  const error = input.error ? freezeDeepSafe(input.error) : undefined;

  const attempt: NotificationDeliveryAttempt = {
    notificationId: input.notificationId,
    attempt: input.attempt,
    status: input.status,
    timestamp: input.timestamp,
    duration: input.duration,
    error
  };

  return freezeDeepSafe(attempt);
}

export function createNotificationDeliveryResult(input: {
  notificationId: string;
  channelId: string;
  status: NotificationDeliveryStatusValue;
  error?: { name: string; message: string; stack?: string };
  attemptedAt: number;
  completedAt: number;
  duration: number;
  attempts: number;
  history: ReadonlyArray<NotificationDeliveryAttempt>;
}): NotificationDeliveryResult {
  if (!input.notificationId) {
    throw new AlertRuleValidationError('Notification ID is required for delivery result');
  }
  if (!input.channelId) {
    throw new AlertRuleValidationError('Channel ID is required for delivery result');
  }
  if (!Object.values(NotificationDeliveryStatus).includes(input.status)) {
    throw new AlertRuleValidationError(`Invalid delivery result status: ${input.status}`);
  }
  if (typeof input.attemptedAt !== 'number' || isNaN(input.attemptedAt) || input.attemptedAt < 0) {
    throw new AlertRuleValidationError('Invalid attemptedAt');
  }
  if (typeof input.completedAt !== 'number' || isNaN(input.completedAt) || input.completedAt < 0) {
    throw new AlertRuleValidationError('Invalid completedAt');
  }
  if (typeof input.duration !== 'number' || isNaN(input.duration) || input.duration < 0) {
    throw new AlertRuleValidationError('Invalid duration');
  }
  if (typeof input.attempts !== 'number' || isNaN(input.attempts) || input.attempts < 0) {
    throw new AlertRuleValidationError('Invalid attempts count');
  }
  if (!Array.isArray(input.history)) {
    throw new AlertRuleValidationError('History array is required');
  }

  const error = input.error ? freezeDeepSafe(input.error) : undefined;
  const history = freezeDeepSafe(input.history);

  const result: NotificationDeliveryResult = {
    notificationId: input.notificationId,
    channelId: input.channelId,
    status: input.status,
    error,
    attemptedAt: input.attemptedAt,
    completedAt: input.completedAt,
    duration: input.duration,
    attempts: input.attempts,
    history
  };

  return freezeDeepSafe(result);
}
