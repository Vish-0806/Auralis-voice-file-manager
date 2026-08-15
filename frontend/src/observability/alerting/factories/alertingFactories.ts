import { AlertValidationError } from '../errors/AlertingErrors';
import { AlertSeverity, AlertSeverityValue } from '../models/severity';
import { AlertState, AlertStateValue, AlertRecord } from '../models/alert';
import { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
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

  // normalizes metadata, defensively copy mutable structures
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

export function createAlertingStatistics(input: {
  registeredAlertCount: number;
}): AlertingStatistics {
  if (typeof input.registeredAlertCount !== 'number' || isNaN(input.registeredAlertCount) || input.registeredAlertCount < 0) {
    throw new AlertValidationError('registeredAlertCount must be a non-negative number');
  }

  const stats: AlertingStatistics = {
    registeredAlertCount: input.registeredAlertCount
  };

  return freezeDeepSafe(stats);
}

export function createAlertingDiagnostics(input: {
  runtimeState: string;
  registeredAlertCount: number;
  generatedAt: number;
}): AlertingDiagnostics {
  if (typeof input.runtimeState !== 'string' || input.runtimeState.trim() === '') {
    throw new AlertValidationError('runtimeState must be a non-empty string');
  }
  if (typeof input.registeredAlertCount !== 'number' || isNaN(input.registeredAlertCount) || input.registeredAlertCount < 0) {
    throw new AlertValidationError('registeredAlertCount must be a non-negative number');
  }
  if (typeof input.generatedAt !== 'number' || isNaN(input.generatedAt) || input.generatedAt < 0) {
    throw new AlertValidationError('generatedAt must be a valid timestamp');
  }

  const diag: AlertingDiagnostics = {
    runtimeState: input.runtimeState,
    registeredAlertCount: input.registeredAlertCount,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(diag);
}
