import { freezeDeepSafe } from '../../../models/monitoring';
import { Span } from '../../../tracing/models/span';
import { TracingTelemetryTrigger, TracingTelemetryRequest } from '../models';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export function createTriggerId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'trig_tt_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10);
  return `trig_tt_${Date.now()}_${rand}`;
}

export function buildTrigger(span: Span): TracingTelemetryTrigger {
  const correlationId = (span.attributes as any)?.correlationId;
  const requestId = (span.attributes as any)?.requestId;

  const normalizedAttributes = span.attributes ? safeNormalizeAndRedact(span.attributes) : {};
  const normalizedEvents = span.events ? span.events.map(ev => ({
    name: ev.name,
    timestamp: ev.timestamp,
    attributes: ev.attributes ? safeNormalizeAndRedact(ev.attributes) : undefined
  })) : [];

  const trigger: TracingTelemetryTrigger = {
    triggerId: createTriggerId(),
    traceId: span.traceId,
    spanId: span.spanId,
    parentSpanId: span.parentSpanId,
    timestamp: Date.now(),
    startTime: span.startTime,
    endTime: span.endTime,
    duration: span.duration ?? (span.endTime ? span.endTime - span.startTime : 0),
    spanName: span.name,
    spanKind: span.kind,
    spanStatus: span.status,
    correlationId,
    requestId,
    attributes: normalizedAttributes,
    events: normalizedEvents,
    error: span.error ? safeNormalizeAndRedact(span.error) : undefined
  };

  return freezeDeepSafe(trigger) as TracingTelemetryTrigger;
}

export function buildRequest(options: {
  telemetryType: string;
  traceId: string;
  spanId: string;
  correlationId?: string;
  requestId?: string;
  name: string;
  duration: number;
  severity: string;
  attributes: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  source: string;
}): TracingTelemetryRequest {
  const request: TracingTelemetryRequest = {
    recordId: 'rec_' + Math.random().toString(36).substring(2, 15),
    telemetryType: options.telemetryType as any,
    timestamp: Date.now(),
    traceId: options.traceId,
    spanId: options.spanId,
    correlationId: options.correlationId,
    requestId: options.requestId,
    name: options.name,
    duration: options.duration,
    severity: options.severity as any,
    attributes: options.attributes,
    metadata: options.metadata,
    source: options.source
  };

  return freezeDeepSafe(request) as TracingTelemetryRequest;
}
