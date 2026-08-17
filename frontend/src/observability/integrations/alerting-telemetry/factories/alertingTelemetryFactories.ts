import {
  AlertingTelemetryTrigger,
  AlertingTelemetryRequest,
  AlertingTelemetryResult,
  AlertingTelemetryPolicy
} from '../models';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';
import { freezeDeepSafe } from '../../../models/monitoring';
import { TelemetryTypeValue } from '../../../telemetry/models/telemetry';

export function buildTrigger(options: Partial<AlertingTelemetryTrigger>): AlertingTelemetryTrigger {
  const trigger = {
    triggerId: options.triggerId || `trg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    kind: options.kind || 'EVALUATED',
    timestamp: options.timestamp || Date.now(),
    alertId: options.alertId,
    fingerprint: options.fingerprint,
    ruleId: options.ruleId,
    sourceId: options.sourceId,
    correlationId: options.correlationId,
    traceId: options.traceId,
    requestId: options.requestId,
    operationId: options.operationId,
    lifecycleState: options.lifecycleState,
    severity: options.severity,
    status: options.status,
    orchestrationStatus: options.orchestrationStatus,
    notificationStatus: options.notificationStatus,
    metadata: options.metadata ? safeNormalizeAndRedact(options.metadata) : {},
    payload: options.payload ? safeNormalizeAndRedact(options.payload) : undefined
  };
  return freezeDeepSafe(trigger) as AlertingTelemetryTrigger;
}

export function buildRequest(options: {
  telemetryType: TelemetryTypeValue;
  timestamp?: number;
  alertId?: string;
  fingerprint?: string;
  ruleId?: string;
  sourceId?: string;
  correlationId?: string;
  requestId?: string;
  operationId?: string;
  traceId?: string;
  name: string;
  severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';
  attributes: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  source: string;
  policy: AlertingTelemetryPolicy;
}): AlertingTelemetryRequest {
  const request = {
    recordId: `rec_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    telemetryType: options.telemetryType,
    timestamp: options.timestamp || Date.now(),
    alertId: options.alertId,
    fingerprint: options.fingerprint,
    ruleId: options.ruleId,
    sourceId: options.sourceId,
    correlationId: options.correlationId,
    requestId: options.requestId,
    operationId: options.operationId,
    traceId: options.traceId,
    name: options.name,
    severity: options.severity,
    attributes: safeNormalizeAndRedact(options.attributes),
    metadata: options.metadata ? safeNormalizeAndRedact(options.metadata) : undefined,
    source: options.source,
    policy: options.policy
  };
  return freezeDeepSafe(request) as AlertingTelemetryRequest;
}

export function buildResult(options: {
  status: 'ACCEPTED' | 'SKIPPED' | 'REJECTED';
  triggerId?: string;
  recordId?: string;
  telemetryType?: TelemetryTypeValue;
  reason?: string;
  duration: number;
  timestamp?: number;
}): AlertingTelemetryResult {
  const result = {
    status: options.status,
    triggerId: options.triggerId,
    recordId: options.recordId,
    telemetryType: options.telemetryType,
    reason: options.reason,
    duration: options.duration,
    timestamp: options.timestamp || Date.now()
  };
  return freezeDeepSafe(result) as AlertingTelemetryResult;
}
