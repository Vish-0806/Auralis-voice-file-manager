import { DiagnosticValidationError } from '../errors/DiagnosticsErrors';
import {
  DiagnosticSeverity,
  DiagnosticSeverityValue,
  DiagnosticStatus,
  DiagnosticStatusValue,
  DiagnosticCategory,
  DiagnosticCategoryValue
} from '../models/diagnostic';
import { DiagnosticSourceDescriptor } from '../models/source';
import { DiagnosticCheck, DiagnosticCheckCallback } from '../models/check';
import { DiagnosticResult, NormalizedErrorInfo } from '../models/result';
import { DiagnosticReport } from '../models/report';
import { DiagnosticsStatistics } from '../models/statistics';

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

export function createDiagnosticSourceDescriptor(input: {
  id: string;
  name: string;
  description: string;
  version?: string | null;
  enabled?: boolean;
  priority?: number;
  metadata?: Record<string, unknown>;
}): DiagnosticSourceDescriptor {
  if (!input.id || typeof input.id !== 'string') {
    throw new DiagnosticValidationError('Diagnostic source id must be a non-empty string');
  }
  if (!input.name || typeof input.name !== 'string') {
    throw new DiagnosticValidationError('Diagnostic source name must be a non-empty string');
  }
  if (!input.description || typeof input.description !== 'string') {
    throw new DiagnosticValidationError('Diagnostic source description must be a non-empty string');
  }

  const descriptor: DiagnosticSourceDescriptor = {
    id: input.id,
    name: input.name,
    description: input.description,
    version: input.version || null,
    enabled: input.enabled !== false,
    priority: typeof input.priority === 'number' ? input.priority : 0,
    metadata: input.metadata ? { ...input.metadata } : {}
  };

  return freezeDeepSafe(descriptor);
}

export function createDiagnosticCheck(input: {
  id: string;
  sourceId: string;
  name: string;
  description: string;
  category: DiagnosticCategoryValue;
  severity: DiagnosticSeverityValue;
  enabled?: boolean;
  timeout?: number;
  priority?: number;
  execute: DiagnosticCheckCallback;
}): DiagnosticCheck {
  if (!input.id || typeof input.id !== 'string') {
    throw new DiagnosticValidationError('Diagnostic check id must be a non-empty string');
  }
  if (!input.sourceId || typeof input.sourceId !== 'string') {
    throw new DiagnosticValidationError('Diagnostic check sourceId must be a non-empty string');
  }
  if (!input.name || typeof input.name !== 'string') {
    throw new DiagnosticValidationError('Diagnostic check name must be a non-empty string');
  }
  if (!input.description || typeof input.description !== 'string') {
    throw new DiagnosticValidationError('Diagnostic check description must be a non-empty string');
  }
  if (!Object.values(DiagnosticCategory).includes(input.category)) {
    throw new DiagnosticValidationError(`Invalid diagnostic check category: ${input.category}`);
  }
  if (!Object.values(DiagnosticSeverity).includes(input.severity)) {
    throw new DiagnosticValidationError(`Invalid diagnostic check severity: ${input.severity}`);
  }
  if (typeof input.execute !== 'function') {
    throw new DiagnosticValidationError('Diagnostic check execute callback must be a function');
  }
  if (input.timeout !== undefined && (typeof input.timeout !== 'number' || input.timeout < 0)) {
    throw new DiagnosticValidationError('Diagnostic check timeout must be a non-negative number');
  }

  const check: DiagnosticCheck = {
    id: input.id,
    sourceId: input.sourceId,
    name: input.name,
    description: input.description,
    category: input.category,
    severity: input.severity,
    enabled: input.enabled !== false,
    timeout: input.timeout,
    priority: typeof input.priority === 'number' ? input.priority : 0,
    execute: input.execute
  };

  return freezeDeepSafe(check);
}

export function createDiagnosticResult(input: {
  checkId: string;
  sourceId: string;
  status: DiagnosticStatusValue;
  severity: DiagnosticSeverityValue;
  message: string;
  duration: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
  error?: NormalizedErrorInfo;
}): DiagnosticResult {
  if (!input.checkId || typeof input.checkId !== 'string') {
    throw new DiagnosticValidationError('Diagnostic result checkId must be a non-empty string');
  }
  if (!input.sourceId || typeof input.sourceId !== 'string') {
    throw new DiagnosticValidationError('Diagnostic result sourceId must be a non-empty string');
  }
  if (!Object.values(DiagnosticStatus).includes(input.status)) {
    throw new DiagnosticValidationError(`Invalid diagnostic result status: ${input.status}`);
  }
  if (!Object.values(DiagnosticSeverity).includes(input.severity)) {
    throw new DiagnosticValidationError(`Invalid diagnostic result severity: ${input.severity}`);
  }
  if (typeof input.duration !== 'number' || input.duration < 0) {
    throw new DiagnosticValidationError('Diagnostic result duration must be a non-negative number');
  }
  if (typeof input.timestamp !== 'number' || input.timestamp < 0) {
    throw new DiagnosticValidationError('Diagnostic result timestamp must be a valid epoch number');
  }

  const result: DiagnosticResult = {
    checkId: input.checkId,
    sourceId: input.sourceId,
    status: input.status,
    severity: input.severity,
    message: input.message || '',
    duration: input.duration,
    timestamp: input.timestamp,
    metadata: input.metadata ? { ...input.metadata } : {},
    error: input.error ? { ...input.error } : undefined
  };

  return freezeDeepSafe(result);
}

export function createDiagnosticReport(input: {
  reportId: string;
  generatedAt: number;
  runtimeState: string;
  overallStatus: DiagnosticStatusValue;
  overallSeverity: DiagnosticSeverityValue;
  sourceCount: number;
  checkCount: number;
  passedCount: number;
  degradedCount: number;
  failedCount: number;
  skippedCount: number;
  results: ReadonlyArray<DiagnosticResult>;
  summary: string;
  statistics: DiagnosticsStatistics;
}): DiagnosticReport {
  if (!input.reportId || typeof input.reportId !== 'string') {
    throw new DiagnosticValidationError('Diagnostic report reportId must be a non-empty string');
  }
  if (typeof input.generatedAt !== 'number' || input.generatedAt < 0) {
    throw new DiagnosticValidationError('Diagnostic report generatedAt must be a valid timestamp');
  }
  if (!Object.values(DiagnosticStatus).includes(input.overallStatus)) {
    throw new DiagnosticValidationError(`Invalid diagnostic report status: ${input.overallStatus}`);
  }
  if (!Object.values(DiagnosticSeverity).includes(input.overallSeverity)) {
    throw new DiagnosticValidationError(`Invalid diagnostic report severity: ${input.overallSeverity}`);
  }
  if (!Array.isArray(input.results)) {
    throw new DiagnosticValidationError('Diagnostic report results must be an array');
  }

  const report: DiagnosticReport = {
    reportId: input.reportId,
    generatedAt: input.generatedAt,
    runtimeState: input.runtimeState,
    overallStatus: input.overallStatus,
    overallSeverity: input.overallSeverity,
    sourceCount: input.sourceCount,
    checkCount: input.checkCount,
    passedCount: input.passedCount,
    degradedCount: input.degradedCount,
    failedCount: input.failedCount,
    skippedCount: input.skippedCount,
    results: input.results,
    summary: input.summary,
    statistics: input.statistics
  };

  return freezeDeepSafe(report);
}

export function createDiagnosticsStatistics(input: {
  totalRuns: number;
  successfulRuns: number;
  degradedRuns: number;
  failedRuns: number;
  skippedChecks: number;
  executedChecks: number;
  failedChecks: number;
  timedOutChecks: number;
  totalDuration: number;
  averageDuration: number;
  sourceCount: number;
  checkCount: number;
}): DiagnosticsStatistics {
  const stats: DiagnosticsStatistics = {
    totalRuns: typeof input.totalRuns === 'number' ? input.totalRuns : 0,
    successfulRuns: typeof input.successfulRuns === 'number' ? input.successfulRuns : 0,
    degradedRuns: typeof input.degradedRuns === 'number' ? input.degradedRuns : 0,
    failedRuns: typeof input.failedRuns === 'number' ? input.failedRuns : 0,
    skippedChecks: typeof input.skippedChecks === 'number' ? input.skippedChecks : 0,
    executedChecks: typeof input.executedChecks === 'number' ? input.executedChecks : 0,
    failedChecks: typeof input.failedChecks === 'number' ? input.failedChecks : 0,
    timedOutChecks: typeof input.timedOutChecks === 'number' ? input.timedOutChecks : 0,
    totalDuration: typeof input.totalDuration === 'number' ? input.totalDuration : 0,
    averageDuration: typeof input.averageDuration === 'number' ? input.averageDuration : 0,
    sourceCount: typeof input.sourceCount === 'number' ? input.sourceCount : 0,
    checkCount: typeof input.checkCount === 'number' ? input.checkCount : 0
  };

  return freezeDeepSafe(stats);
}

export function createDiagnosticsSnapshot(input: {
  runtimeState: string;
  sourceCount: number;
  enabledSourceCount: number;
  checkCount: number;
  enabledCheckCount: number;
  historySize: number;
  statistics: DiagnosticsStatistics;
  generatedAt: number;
}) {
  const snapshot = {
    runtimeState: input.runtimeState,
    sourceCount: input.sourceCount,
    enabledSourceCount: input.enabledSourceCount,
    checkCount: input.checkCount,
    enabledCheckCount: input.enabledCheckCount,
    historySize: input.historySize,
    statistics: input.statistics,
    generatedAt: input.generatedAt
  };

  return freezeDeepSafe(snapshot);
}
