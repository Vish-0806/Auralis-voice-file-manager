import { freezeDeepSafe } from '../../../models/monitoring';
import { DiagnosticReport } from '../../../diagnostics/models/report';
import { DiagnosticResult } from '../../../diagnostics/models/result';
import { DiagnosticsTelemetryTrigger, DiagnosticsTelemetryRequest } from '../models';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';
import { DiagnosticSeverity, DiagnosticStatus } from '../../../diagnostics/models/diagnostic';

export function createTriggerId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'trig_dt_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10);
  return `trig_dt_${Date.now()}_${rand}`;
}

export function validateSeverity(severity: string): void {
  const valid = Object.values(DiagnosticSeverity);
  if (!valid.includes(severity as any)) {
    throw new Error(`Invalid diagnostic severity: ${severity}. Must be one of ${valid.join(', ')}`);
  }
}

export function validateStatus(status: string): void {
  const valid = Object.values(DiagnosticStatus);
  if (!valid.includes(status as any)) {
    throw new Error(`Invalid diagnostic status: ${status}. Must be one of ${valid.join(', ')}`);
  }
}

export function buildTriggerFromReport(report: DiagnosticReport): DiagnosticsTelemetryTrigger {
  validateSeverity(report.overallSeverity);
  validateStatus(report.overallStatus);

  const correlationId = (report.statistics as any)?.correlationId;
  const requestId = (report.statistics as any)?.requestId;

  const trigger: DiagnosticsTelemetryTrigger = {
    triggerId: createTriggerId(),
    diagnosticRunId: report.reportId,
    sourceId: 'diagnostics-system',
    timestamp: Date.now(),
    startedAt: report.generatedAt,
    completedAt: report.generatedAt,
    duration: 0,
    sourceName: 'Diagnostics Run Report',
    diagnosticSeverity: report.overallSeverity,
    diagnosticStatus: report.overallStatus,
    message: report.summary,
    correlationId,
    requestId,
    metadata: report.statistics ? safeNormalizeAndRedact(report.statistics) : {}
  };

  return freezeDeepSafe(trigger) as DiagnosticsTelemetryTrigger;
}

export function buildTriggerFromResult(
  result: DiagnosticResult,
  diagnosticRunId: string
): DiagnosticsTelemetryTrigger {
  validateSeverity(result.severity);
  validateStatus(result.status);

  const correlationId = (result.metadata as any)?.correlationId;
  const requestId = (result.metadata as any)?.requestId;
  const operationId = (result.metadata as any)?.operationId;
  const traceId = (result.metadata as any)?.traceId;

  const normalizedMetadata = result.metadata ? safeNormalizeAndRedact(result.metadata) : {};

  const trigger: DiagnosticsTelemetryTrigger = {
    triggerId: createTriggerId(),
    diagnosticRunId,
    resultId: `${result.sourceId}/${result.checkId}`,
    sourceId: result.sourceId,
    checkId: result.checkId,
    timestamp: Date.now(),
    startedAt: result.timestamp - result.duration,
    completedAt: result.timestamp,
    duration: result.duration,
    sourceName: result.sourceId,
    checkName: result.checkId,
    diagnosticSeverity: result.severity,
    diagnosticStatus: result.status,
    message: result.message,
    correlationId,
    requestId,
    operationId,
    traceId,
    metadata: normalizedMetadata,
    error: result.error ? safeNormalizeAndRedact(result.error) : undefined
  };

  return freezeDeepSafe(trigger) as DiagnosticsTelemetryTrigger;
}

export function buildRequest(options: {
  telemetryType: string;
  diagnosticRunId: string;
  resultId?: string;
  sourceId: string;
  checkId?: string;
  correlationId?: string;
  requestId?: string;
  operationId?: string;
  traceId?: string;
  name: string;
  severity: string;
  status: string;
  attributes: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  source: string;
}): DiagnosticsTelemetryRequest {
  const request: DiagnosticsTelemetryRequest = {
    recordId: 'rec_' + Math.random().toString(36).substring(2, 15),
    telemetryType: options.telemetryType as any,
    timestamp: Date.now(),
    diagnosticRunId: options.diagnosticRunId,
    resultId: options.resultId,
    sourceId: options.sourceId,
    checkId: options.checkId,
    correlationId: options.correlationId,
    requestId: options.requestId,
    operationId: options.operationId,
    traceId: options.traceId,
    name: options.name,
    severity: options.severity as any,
    status: options.status,
    attributes: options.attributes,
    metadata: options.metadata,
    source: options.source
  };

  return freezeDeepSafe(request) as DiagnosticsTelemetryRequest;
}
